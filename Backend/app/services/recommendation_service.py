from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.recommendation_repository import recommendation_repo
from app.schemas.recommendation import RecommendationCreate, RecommendationUpdate
from app.models.recommendation import Recommendation

class RecommendationService:
    def create_recommendation(self, db: Session, rec_in: RecommendationCreate) -> Recommendation:
        return recommendation_repo.create(db, obj_in=rec_in)

    def get_active_recommendations(self, db: Session, user_id: int, skip: int = 0, limit: int = 50) -> List[Recommendation]:
        return recommendation_repo.get_active_for_user(db, user_id=user_id, skip=skip, limit=limit)

    def dismiss_recommendation(self, db: Session, rec_id: int) -> Optional[Recommendation]:
        rec = recommendation_repo.get(db, id=rec_id)
        if rec:
            return recommendation_repo.update(db, db_obj=rec, obj_in=RecommendationUpdate(status="dismissed"))
        return None

    def act_on_recommendation(self, db: Session, rec_id: int) -> Optional[Recommendation]:
        rec = recommendation_repo.get(db, id=rec_id)
        if rec:
            return recommendation_repo.update(db, db_obj=rec, obj_in=RecommendationUpdate(status="acted"))
        return None

recommendation_service = RecommendationService()
