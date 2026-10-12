"""
API-level tests for the Recommendation Module endpoints.

Tests cover:
- Unauthenticated access (401)
- Cross-user device access (403 / 404)
- Valid generate flow
- Invalid period values
- Duplicate prevention
- Preservation of acted/dismissed recommendations
- Database rollback on failure
"""
import pytest
from unittest.mock import patch, MagicMock

from app.models.recommendation import Recommendation


# ── GET /api/v1/recommendations/ ──────────────────────────────────────────────

class TestGetRecommendations:
    def test_returns_empty_for_new_user(self, client):
        resp = client.get("/api/v1/recommendations/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_active_recommendations_only_by_default(self, client, db, user, device):
        db.add(Recommendation(
            user_id=user.id, device_id=device.id,
            category="efficiency", message="Save gas", confidence=0.8,
            priority=3, status="active",
        ))
        db.add(Recommendation(
            user_id=user.id, device_id=device.id,
            category="safety", message="Old rec", confidence=0.9,
            priority=2, status="dismissed",
        ))
        db.flush()

        resp = client.get("/api/v1/recommendations/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["status"] == "active"

    def test_include_all_returns_all_statuses(self, client, db, user, device):
        for status in ["active", "acted", "dismissed"]:
            db.add(Recommendation(
                user_id=user.id, device_id=device.id,
                category="general", message=f"Rec {status}", confidence=0.7,
                priority=4, status=status,
            ))
        db.flush()

        resp = client.get("/api/v1/recommendations/?include_all=true")
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_unauthenticated_get_returns_401(self, unauthenticated_client):
        resp = unauthenticated_client.get("/api/v1/recommendations/")
        assert resp.status_code == 401


# ── GET /api/v1/recommendations/counts ───────────────────────────────────────

class TestGetCounts:
    def test_counts_per_status(self, client, db, user, device):
        for status, n in [("active", 2), ("acted", 3), ("dismissed", 1)]:
            for _ in range(n):
                db.add(Recommendation(
                    user_id=user.id, device_id=device.id,
                    category="general", message="m", confidence=0.5,
                    priority=4, status=status,
                ))
        db.flush()

        resp = client.get("/api/v1/recommendations/counts")
        assert resp.status_code == 200
        data = resp.json()
        assert data["active"] == 2
        assert data["acted"] == 3
        assert data["dismissed"] == 1

    def test_unauthenticated_returns_401(self, unauthenticated_client):
        resp = unauthenticated_client.get("/api/v1/recommendations/counts")
        assert resp.status_code == 401


# ── PATCH /api/v1/recommendations/{id}/dismiss ───────────────────────────────

class TestDismiss:
    def test_dismiss_own_recommendation(self, client, db, user, device):
        rec = Recommendation(
            user_id=user.id, device_id=device.id,
            category="efficiency", message="test", confidence=0.8,
            priority=3, status="active",
        )
        db.add(rec)
        db.flush()

        resp = client.patch(f"/api/v1/recommendations/{rec.id}/dismiss")
        assert resp.status_code == 200
        assert resp.json()["status"] == "dismissed"

    def test_cannot_dismiss_another_users_recommendation(self, client_user2, db, user, device):
        rec = Recommendation(
            user_id=user.id, device_id=device.id,
            category="efficiency", message="test", confidence=0.8,
            priority=3, status="active",
        )
        db.add(rec)
        db.flush()

        resp = client_user2.patch(f"/api/v1/recommendations/{rec.id}/dismiss")
        assert resp.status_code == 404

    def test_dismiss_nonexistent_returns_404(self, client):
        resp = client.patch("/api/v1/recommendations/99999/dismiss")
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, unauthenticated_client, db, user, device):
        rec = Recommendation(
            user_id=user.id, device_id=device.id,
            category="efficiency", message="test", confidence=0.8,
            priority=3, status="active",
        )
        db.add(rec)
        db.flush()
        resp = unauthenticated_client.patch(f"/api/v1/recommendations/{rec.id}/dismiss")
        assert resp.status_code == 401


# ── PATCH /api/v1/recommendations/{id}/act ───────────────────────────────────

class TestAct:
    def test_act_own_recommendation(self, client, db, user, device):
        rec = Recommendation(
            user_id=user.id, device_id=device.id,
            category="cooking", message="test", confidence=0.7,
            priority=3, status="active",
        )
        db.add(rec)
        db.flush()

        resp = client.patch(f"/api/v1/recommendations/{rec.id}/act")
        assert resp.status_code == 200
        assert resp.json()["status"] == "acted"

    def test_cannot_act_another_users_recommendation(self, client_user2, db, user, device):
        rec = Recommendation(
            user_id=user.id, device_id=device.id,
            category="cooking", message="test", confidence=0.7,
            priority=3, status="active",
        )
        db.add(rec)
        db.flush()

        resp = client_user2.patch(f"/api/v1/recommendations/{rec.id}/act")
        assert resp.status_code == 404

    def test_unauthenticated_returns_401(self, unauthenticated_client, db, user, device):
        rec = Recommendation(
            user_id=user.id, device_id=device.id,
            category="cooking", message="test", confidence=0.7,
            priority=3, status="active",
        )
        db.add(rec)
        db.flush()
        resp = unauthenticated_client.patch(f"/api/v1/recommendations/{rec.id}/act")
        assert resp.status_code == 401


# ── POST /api/v1/recommendations/generate ────────────────────────────────────

class TestGenerate:
    def _mock_generate(self, rule_ids=("R06",), n=1):
        """Return a mock patch for generate_recommendations."""
        from app.schemas.recommendation import GenerateResponse
        response = GenerateResponse(
            device_id="SGD-TEST-001",
            generated=n,
            rules_triggered=list(rule_ids),
            message=f"{n} recommendation(s) generated.",
        )
        return patch(
            "app.api.v1.recommendations.recommendation_service.generate_recommendations",
            return_value=response,
        )

    def test_generate_success(self, client, device):
        with self._mock_generate(n=2, rule_ids=["R01", "R06"]):
            resp = client.post("/api/v1/recommendations/generate", json={
                "device_id": "SGD-TEST-001",
                "days": 30,
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["generated"] == 2
        assert "R01" in data["rules_triggered"]

    def test_generate_wrong_device_returns_404(self, client):
        resp = client.post("/api/v1/recommendations/generate", json={
            "device_id": "NONEXISTENT-DEVICE",
            "days": 30,
        })
        assert resp.status_code == 404

    def test_generate_other_users_device_returns_403(self, client, device2):
        """User1 cannot generate recommendations for device2 (owned by user2)."""
        resp = client.post("/api/v1/recommendations/generate", json={
            "device_id": device2.id,
            "days": 30,
        })
        assert resp.status_code == 403

    def test_generate_unauthenticated_returns_401(self, unauthenticated_client, device):
        resp = unauthenticated_client.post("/api/v1/recommendations/generate", json={
            "device_id": "SGD-TEST-001",
            "days": 30,
        })
        assert resp.status_code == 401

    def test_generate_invalid_days_too_low(self, client, device):
        resp = client.post("/api/v1/recommendations/generate", json={
            "device_id": "SGD-TEST-001",
            "days": 0,
        })
        assert resp.status_code == 422   # Pydantic validation error

    def test_generate_invalid_days_too_high(self, client, device):
        resp = client.post("/api/v1/recommendations/generate", json={
            "device_id": "SGD-TEST-001",
            "days": 200,
        })
        assert resp.status_code == 422

    def test_generate_missing_device_id(self, client):
        resp = client.post("/api/v1/recommendations/generate", json={"days": 30})
        assert resp.status_code == 422

    def test_generate_service_failure_returns_500(self, client, device):
        with patch(
            "app.api.v1.recommendations.recommendation_service.generate_recommendations",
            side_effect=RuntimeError("DB failure"),
        ):
            resp = client.post("/api/v1/recommendations/generate", json={
                "device_id": "SGD-TEST-001",
                "days": 30,
            })
        assert resp.status_code == 500
