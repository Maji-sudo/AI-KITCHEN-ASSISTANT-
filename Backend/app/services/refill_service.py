from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.refill_repository import refill_prediction_repo
from app.schemas.refill import RefillPredictionCreate
from app.models.refill_prediction import RefillPrediction

class RefillService:
    def create_prediction(self, db: Session, pred_in: RefillPredictionCreate) -> RefillPrediction:
        """Store a newly computed refill prediction."""
        return refill_prediction_repo.create(db, obj_in=pred_in)

    def get_latest_prediction(self, db: Session, device_id: str) -> Optional[RefillPrediction]:
        """Get the most recent prediction for a device."""
        return refill_prediction_repo.get_latest_for_device(db, device_id=device_id)

    def get_prediction_history(self, db: Session, device_id: str, limit: int = 10) -> List[RefillPrediction]:
        """Get historical refill predictions for a device."""
        return refill_prediction_repo.get_all_for_device(db, device_id=device_id, limit=limit)

refill_service = RefillService()
