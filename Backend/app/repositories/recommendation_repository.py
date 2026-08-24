from typing import List
from sqlalchemy.orm import Session
from app.repositories.base_repository import CRUDBase
from app.models.recommendation import Recommendation
from app.schemas.recommendation import RecommendationCreate, RecommendationUpdate

class RecommendationRepository(CRUDBase[Recommendation, RecommendationCreate, RecommendationUpdate]):
    def get_active_for_user(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 50) -> List[Recommendation]:
        return (
            db.query(Recommendation)
            .filter(Recommendation.user_id == user_id, Recommendation.status == "active")
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_device(self, db: Session, *, device_id: str, skip: int = 0, limit: int = 50) -> List[Recommendation]:
        return (
            db.query(Recommendation)
            .filter(Recommendation.device_id == device_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

recommendation_repo = RecommendationRepository(Recommendation)
