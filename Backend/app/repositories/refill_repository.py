from typing import List
from sqlalchemy.orm import Session
from app.repositories.base_repository import CRUDBase
from app.models.refill_prediction import RefillPrediction
from app.schemas.refill import RefillPredictionCreate
from pydantic import BaseModel

class RefillPredictionRepository(CRUDBase[RefillPrediction, RefillPredictionCreate, BaseModel]):
    def get_latest_for_device(self, db: Session, *, device_id: str) -> RefillPrediction:
        return (
            db.query(RefillPrediction)
            .filter(RefillPrediction.device_id == device_id)
            .order_by(RefillPrediction.computed_at.desc())
            .first()
        )

    def get_all_for_device(self, db: Session, *, device_id: str, limit: int = 10) -> List[RefillPrediction]:
        return (
            db.query(RefillPrediction)
            .filter(RefillPrediction.device_id == device_id)
            .order_by(RefillPrediction.computed_at.desc())
            .limit(limit)
            .all()
        )

refill_prediction_repo = RefillPredictionRepository(RefillPrediction)
