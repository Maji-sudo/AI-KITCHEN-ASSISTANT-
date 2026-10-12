"""
SafeGas AI — Recommendation Service
====================================
Orchestrates the rule engine, repository CRUD, analytics, and refill service.
All database writes in generate_recommendations() are wrapped in a transaction
that rolls back on any failure — no partial results are left in the database.
"""

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.repositories.recommendation_repository import recommendation_repo
from app.repositories.cooking_repository import cooking_history_repo
from app.schemas.recommendation import RecommendationCreate, RecommendationUpdate, GenerateResponse
from app.models.recommendation import Recommendation
from app.models.user import User
from app.services.recommendation_engine import recommendation_engine, RuleOutput
from app.services.analytics_service import analytics_service
from app.services.refill_service import refill_service

logger = logging.getLogger(__name__)


class RecommendationService:

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------

    def get_active_recommendations(
        self,
        db: Session,
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Recommendation]:
        """Return active recommendations for the authenticated user, priority-sorted."""
        return recommendation_repo.get_active_for_user(
            db, user_id=user_id, skip=skip, limit=limit
        )

    def get_all_recommendations(
        self,
        db: Session,
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Recommendation]:
        """Return all recommendations (all statuses) for a user."""
        return recommendation_repo.get_all_for_user(
            db, user_id=user_id, skip=skip, limit=limit
        )

    def get_counts(self, db: Session, *, user_id: int) -> dict:
        """Return {active, acted, dismissed} counts for dashboard summary bar."""
        return recommendation_repo.count_by_status_for_user(db, user_id=user_id)

    # ------------------------------------------------------------------
    # STATUS TRANSITIONS (ownership always verified server-side)
    # ------------------------------------------------------------------

    def dismiss_recommendation(
        self, db: Session, *, rec_id: int, user_id: int
    ) -> Optional[Recommendation]:
        rec = recommendation_repo.get(db, id=rec_id)
        if rec is None or rec.user_id != user_id:
            return None
        return recommendation_repo.update(
            db, db_obj=rec, obj_in=RecommendationUpdate(status="dismissed")
        )

    def act_on_recommendation(
        self, db: Session, *, rec_id: int, user_id: int
    ) -> Optional[Recommendation]:
        rec = recommendation_repo.get(db, id=rec_id)
        if rec is None or rec.user_id != user_id:
            return None
        return recommendation_repo.update(
            db, db_obj=rec, obj_in=RecommendationUpdate(status="acted")
        )

    # ------------------------------------------------------------------
    # GENERATE — core orchestration
    # ------------------------------------------------------------------

    def generate_recommendations(
        self,
        db: Session,
        *,
        current_user: User,
        device_id: str,
        days: int = 30,
    ) -> GenerateResponse:
        """
        1. Fetch full analytics summary for the device.
        2. Fetch recent cooking history (last 30 sessions).
        3. Fetch the latest refill prediction if one exists.
        4. Run the deterministic rule engine.
        5. In a single transaction:
           a. Delete all 'active' recommendations for the device
              (acted/dismissed records are preserved).
           b. Insert each RuleOutput as a new Recommendation row.
           c. Commit — or roll back the entire batch on any failure.
        6. Return a GenerateResponse.

        The caller must NOT wrap this call in a separate transaction;
        this method owns the transaction boundary for step 5.
        """
        # ── 1. Analytics summary ─────────────────────────────────────────
        summary = analytics_service.get_full_summary(
            db, device_id=device_id, days=days
        )

        # ── 2. Cooking history ───────────────────────────────────────────
        cooking_hist = cooking_history_repo.get_by_device(
            db, device_id=device_id, limit=30
        )

        # ── 3. Refill prediction (optional — engine skips R09 if None) ───
        try:
            latest_refill = refill_service.get_latest_prediction(db, device_id=device_id)
        except Exception:
            logger.warning(
                "Could not fetch refill prediction for device=%s — R09 will be skipped",
                device_id,
            )
            latest_refill = None

        # ── 4. Run engine ────────────────────────────────────────────────
        outputs: List[RuleOutput] = recommendation_engine.evaluate(
            summary, cooking_hist, latest_refill
        )

        # ── 5. Transactional write ───────────────────────────────────────
        try:
            # 5a. Delete stale active recommendations
            deleted_count = recommendation_repo.delete_stale_active_for_device(
                db, device_id=device_id
            )
            logger.debug(
                "Deleted %d stale active recommendations for device=%s",
                deleted_count,
                device_id,
            )

            # 5b. Insert new recommendations (without individual commits)
            new_recs: List[Recommendation] = []
            for out in outputs:
                rec_in = RecommendationCreate(
                    user_id=int(current_user.id),
                    device_id=device_id,
                    category=out.category,
                    message=out.message,
                    supporting_facts_json=out.supporting_facts,
                    confidence=out.confidence,
                    priority=out.priority,
                    status="active",
                )
                obj_data = rec_in.model_dump()
                db_obj = Recommendation(**{
                    k: v for k, v in obj_data.items()
                    if hasattr(Recommendation, k)
                })
                db.add(db_obj)
                new_recs.append(db_obj)

            # 5c. Single commit for the whole batch
            db.commit()
            for obj in new_recs:
                db.refresh(obj)

        except Exception as exc:
            db.rollback()
            logger.error(
                "generate_recommendations transaction failed for device=%s: %s",
                device_id,
                exc,
            )
            raise

        rule_ids = [o.rule_id for o in outputs]
        logger.info(
            "Generated %d recommendation(s) for user=%s device=%s rules=%s",
            len(outputs),
            current_user.id,
            device_id,
            rule_ids,
        )

        return GenerateResponse(
            device_id=device_id,
            generated=len(outputs),
            rules_triggered=rule_ids,
            message=(
                f"{len(outputs)} personalised recommendation(s) generated."
                if outputs
                else "No new recommendations — your LPG usage looks optimal!"
            ),
        )


recommendation_service = RecommendationService()
