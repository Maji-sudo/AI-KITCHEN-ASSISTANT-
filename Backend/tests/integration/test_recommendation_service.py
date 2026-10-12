"""
Integration tests for RecommendationService.generate_recommendations().

Tests:
- Repeated generation replaces active recommendations (duplicate prevention)
- Acted and dismissed recommendations are preserved across regeneration
- DB rollback on failure leaves no partial results
- Correct rules fire based on analytics signals
"""
import pytest
from unittest.mock import patch, MagicMock

from app.models.recommendation import Recommendation
from app.services.recommendation_service import recommendation_service
from app.services.recommendation_engine import RuleOutput


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_rule_output(rule_id: str = "R06", category: str = "efficiency") -> RuleOutput:
    return RuleOutput(
        rule_id=rule_id,
        category=category,
        priority=3,
        confidence=0.80,
        message=f"Test message for {rule_id}",
        supporting_facts={"test": True},
    )


import app.services.recommendation_service as _rec_svc_mod
from app.services.recommendation_engine import recommendation_engine as _engine_singleton
from app.services.analytics_service import analytics_service as _analytics_service
from app.services.refill_service import refill_service as _refill_service
from app.repositories.cooking_repository import cooking_history_repo as _cooking_history_repo


def _mock_engine(outputs: list):
    """Patch the engine's evaluate() method directly on the singleton object."""
    return patch.object(
        _engine_singleton,
        "evaluate",
        return_value=outputs,
    )


def _mock_analytics():
    """Patch analytics_service.get_full_summary on the singleton object."""
    mock_summary = MagicMock()
    mock_summary.device_id = "SGD-TEST-001"
    mock_summary.period_days = 30
    return patch.object(
        _analytics_service,
        "get_full_summary",
        return_value=mock_summary,
    )


def _mock_refill(days_left=None):
    """Patch refill_service.get_latest_prediction on the singleton object."""
    if days_left is None:
        pred = None
    else:
        pred = MagicMock()
        pred.days_left = days_left
        pred.confidence = 0.88
        from datetime import datetime, timezone, timedelta
        pred.predicted_empty_date = datetime.now(timezone.utc) + timedelta(days=days_left)
    return patch.object(
        _refill_service,
        "get_latest_prediction",
        return_value=pred,
    )


def _mock_cooking():
    return patch.object(
        _cooking_history_repo,
        "get_by_device",
        return_value=[],
    )


# ── Duplicate prevention ──────────────────────────────────────────────────────

class TestDuplicatePrevention:
    def test_repeated_generate_replaces_active_recs(self, db, user, device):
        """Calling generate twice should NOT accumulate active recommendations."""
        output = [_make_rule_output("R06")]

        with _mock_analytics(), _mock_refill(), _mock_cooking(), _mock_engine(output):
            recommendation_service.generate_recommendations(
                db, current_user=user, device_id=device.id, days=30
            )

        active_after_first = (
            db.query(Recommendation)
            .filter(Recommendation.device_id == device.id, Recommendation.status == "active")
            .count()
        )
        assert active_after_first == 1

        # Second call with two outputs
        output2 = [_make_rule_output("R03"), _make_rule_output("R06")]
        with _mock_analytics(), _mock_refill(), _mock_cooking(), _mock_engine(output2):
            recommendation_service.generate_recommendations(
                db, current_user=user, device_id=device.id, days=30
            )

        active_after_second = (
            db.query(Recommendation)
            .filter(Recommendation.device_id == device.id, Recommendation.status == "active")
            .count()
        )
        assert active_after_second == 2   # replaced, not accumulated

    def test_total_recommendations_do_not_grow_unboundedly(self, db, user, device):
        """Total row count should equal engine outputs after each run."""
        for run in range(3):
            output = [_make_rule_output(f"R0{i}") for i in range(1, run + 2)]
            with _mock_analytics(), _mock_refill(), _mock_cooking(), _mock_engine(output):
                recommendation_service.generate_recommendations(
                    db, current_user=user, device_id=device.id, days=30
                )

        # After 3 runs with 1, 2, 3 outputs respectively, only last batch stays active
        active = (
            db.query(Recommendation)
            .filter(Recommendation.device_id == device.id, Recommendation.status == "active")
            .count()
        )
        assert active == 3


# ── Preservation of acted / dismissed ────────────────────────────────────────

class TestPreservation:
    def test_acted_recommendations_survive_regeneration(self, db, user, device):
        acted_rec = Recommendation(
            user_id=user.id, device_id=device.id,
            category="efficiency", message="Old acted", confidence=0.8,
            priority=3, status="acted",
        )
        db.add(acted_rec)
        db.flush()
        acted_id = acted_rec.id

        output = [_make_rule_output("R06")]
        with _mock_analytics(), _mock_refill(), _mock_cooking(), _mock_engine(output):
            recommendation_service.generate_recommendations(
                db, current_user=user, device_id=device.id, days=30
            )

        survived = db.query(Recommendation).filter(Recommendation.id == acted_id).first()
        assert survived is not None
        assert survived.status == "acted"

    def test_dismissed_recommendations_survive_regeneration(self, db, user, device):
        dismissed_rec = Recommendation(
            user_id=user.id, device_id=device.id,
            category="safety", message="Old dismissed", confidence=0.9,
            priority=2, status="dismissed",
        )
        db.add(dismissed_rec)
        db.flush()
        dismissed_id = dismissed_rec.id

        output = [_make_rule_output("R01", "safety")]
        with _mock_analytics(), _mock_refill(), _mock_cooking(), _mock_engine(output):
            recommendation_service.generate_recommendations(
                db, current_user=user, device_id=device.id, days=30
            )

        survived = db.query(Recommendation).filter(Recommendation.id == dismissed_id).first()
        assert survived is not None
        assert survived.status == "dismissed"

    def test_only_active_recs_are_deleted(self, db, user, device):
        for status in ["active", "acted", "dismissed"]:
            db.add(Recommendation(
                user_id=user.id, device_id=device.id,
                category="general", message=f"Old {status}", confidence=0.5,
                priority=4, status=status,
            ))
        db.flush()

        with _mock_analytics(), _mock_refill(), _mock_cooking(), _mock_engine([]):
            recommendation_service.generate_recommendations(
                db, current_user=user, device_id=device.id, days=30
            )

        total = db.query(Recommendation).filter(Recommendation.device_id == device.id).count()
        assert total == 2   # acted + dismissed remain; active was deleted


# ── DB rollback on failure ─────────────────────────────────────────────────────

class TestTransactionRollback:
    def test_rollback_on_create_failure_leaves_no_partial_results(self, db, user, device):
        """
        If inserting a new Recommendation fails mid-batch, the transaction
        rolls back and no new rows should be left in the database.
        """
        # Pre-existing active rec
        existing = Recommendation(
            user_id=user.id, device_id=device.id,
            category="efficiency", message="Pre-existing", confidence=0.7,
            priority=3, status="active",
        )
        db.add(existing)
        db.flush()
        existing_id = existing.id

        output = [_make_rule_output("R06"), _make_rule_output("R03")]

        with _mock_analytics(), _mock_refill(), _mock_cooking(), _mock_engine(output):
            # Force db.commit() to raise after the delete but during the insert
            original_commit = db.commit
            call_count = [0]

            def failing_commit():
                call_count[0] += 1
                if call_count[0] == 1:
                    raise RuntimeError("Simulated DB failure")
                return original_commit()

            db.commit = failing_commit
            try:
                with pytest.raises(RuntimeError, match="Simulated DB failure"):
                    recommendation_service.generate_recommendations(
                        db, current_user=user, device_id=device.id, days=30
                    )
            finally:
                db.commit = original_commit

        # After rollback: original state should be intact (per-test rollback fixture)
        # The session is already rolled back by the service; verify no orphan rows exist
        orphan_count = (
            db.query(Recommendation)
            .filter(
                Recommendation.device_id == device.id,
                Recommendation.message.in_(["Test message for R06", "Test message for R03"]),
            )
            .count()
        )
        assert orphan_count == 0


# ── Generate response content ─────────────────────────────────────────────────

class TestGenerateResponse:
    def test_response_contains_rule_ids(self, db, user, device):
        output = [
            _make_rule_output("R01", "safety"),
            _make_rule_output("R05", "efficiency"),
        ]
        with _mock_analytics(), _mock_refill(), _mock_cooking(), _mock_engine(output):
            resp = recommendation_service.generate_recommendations(
                db, current_user=user, device_id=device.id, days=30
            )

        assert resp.generated == 2
        assert set(resp.rules_triggered) == {"R01", "R05"}
        assert "2" in resp.message

    def test_response_message_when_no_rules_fire(self, db, user, device):
        with _mock_analytics(), _mock_refill(), _mock_cooking(), _mock_engine([]):
            resp = recommendation_service.generate_recommendations(
                db, current_user=user, device_id=device.id, days=30
            )

        assert resp.generated == 0
        assert resp.rules_triggered == []
        assert "optimal" in resp.message.lower()

    def test_response_device_id_matches_input(self, db, user, device):
        with _mock_analytics(), _mock_refill(), _mock_cooking(), _mock_engine([]):
            resp = recommendation_service.generate_recommendations(
                db, current_user=user, device_id=device.id, days=30
            )

        assert resp.device_id == device.id
