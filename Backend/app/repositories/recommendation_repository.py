from typing import List
from sqlalchemy.orm import Session

from app.repositories.base_repository import CRUDBase
from app.models.recommendation import Recommendation
from app.schemas.recommendation import RecommendationCreate, RecommendationUpdate


class RecommendationRepository(CRUDBase[Recommendation, RecommendationCreate, RecommendationUpdate]):

    # ------------------------------------------------------------------
    # READ helpers
    # ------------------------------------------------------------------

    def get_active_for_user(
        self,
        db: Session,
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Recommendation]:
        """Return all active recommendations for a user, sorted by priority then date."""
        return (
            db.query(Recommendation)
            .filter(Recommendation.user_id == user_id, Recommendation.status == "active")
            .order_by(Recommendation.priority.asc(), Recommendation.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_all_for_user(
        self,
        db: Session,
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Recommendation]:
        """Return all recommendations for a user (all statuses), newest first."""
        return (
            db.query(Recommendation)
            .filter(Recommendation.user_id == user_id)
            .order_by(Recommendation.priority.asc(), Recommendation.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_device(
        self,
        db: Session,
        *,
        device_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Recommendation]:
        return (
            db.query(Recommendation)
            .filter(Recommendation.device_id == device_id)
            .order_by(Recommendation.priority.asc(), Recommendation.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_active_by_device(
        self,
        db: Session,
        *,
        device_id: str,
    ) -> List[Recommendation]:
        """Return active recommendations for a specific device, sorted by priority."""
        return (
            db.query(Recommendation)
            .filter(Recommendation.device_id == device_id, Recommendation.status == "active")
            .order_by(Recommendation.priority.asc(), Recommendation.created_at.desc())
            .all()
        )

    # ------------------------------------------------------------------
    # DEDUPLICATION / CLEANUP
    # ------------------------------------------------------------------

    def delete_stale_active_for_device(self, db: Session, *, device_id: str) -> int:
        """
        Delete all 'active' recommendations for a device before regenerating.
        Preserves 'acted' and 'dismissed' records for audit history.
        Returns the count of deleted rows.
        """
        deleted = (
            db.query(Recommendation)
            .filter(
                Recommendation.device_id == device_id,
                Recommendation.status == "active",
            )
            .all()
        )
        count = len(deleted)
        for rec in deleted:
            db.delete(rec)
        db.commit()
        return count

    def exists_active_for_category(
        self,
        db: Session,
        *,
        device_id: str,
        category: str,
    ) -> bool:
        """Check whether an active recommendation of a given category already exists."""
        return (
            db.query(Recommendation)
            .filter(
                Recommendation.device_id == device_id,
                Recommendation.category == category,
                Recommendation.status == "active",
            )
            .first()
            is not None
        )

    def count_by_status_for_user(self, db: Session, *, user_id: int) -> dict:
        """Return a dict of {status: count} for a user's recommendations."""
        rows = (
            db.query(Recommendation.status)
            .filter(Recommendation.user_id == user_id)
            .all()
        )
        counts: dict = {"active": 0, "acted": 0, "dismissed": 0}
        for (status,) in rows:
            if status in counts:
                counts[status] += 1
        return counts


recommendation_repo = RecommendationRepository(Recommendation)
