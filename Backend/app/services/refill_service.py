from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.refill_repository import refill_prediction_repo
from app.repositories.telemetry_repository import weight_reading_repo
from app.models.cylinder import Cylinder
from app.models.usage_analytics import UsageAnalytics
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

    def compute_refill_prediction(self, db: Session, device_id: str) -> RefillPrediction:
        """
        Dynamically calculate remaining days and predicted empty date from
        cylinder tare/gross weight and actual consumption rates.
        """
        # 1. Fetch cylinder config (default: standard 14.2kg cylinder)
        cylinder = db.query(Cylinder).filter(Cylinder.device_id == device_id).first()
        tare_weight = cylinder.tare_weight_g if cylinder else 15300.0
        full_weight = cylinder.full_weight_g if cylinder else 29500.0
        net_capacity = full_weight - tare_weight  # typically 14200g

        # 2. Fetch latest weight reading
        latest_weights = weight_reading_repo.get_latest_for_device(db, device_id=device_id, limit=1)
        if latest_weights:
            current_total_weight = latest_weights[0].weight_g
        else:
            current_total_weight = full_weight

        current_net_gas = max(0.0, current_total_weight - tare_weight)

        # 3. Calculate burn rate (grams per day) from usage analytics
        recent_analytics = (
            db.query(UsageAnalytics)
            .filter(UsageAnalytics.device_id == device_id)
            .order_by(UsageAnalytics.period_start.desc())
            .limit(7)
            .all()
        )
        if recent_analytics and len(recent_analytics) > 0:
            avg_daily_burn = sum(a.total_consumption_g for a in recent_analytics) / len(recent_analytics)
            if avg_daily_burn <= 10:
                avg_daily_burn = 350.0
            confidence = min(0.96, 0.75 + (len(recent_analytics) * 0.03))
        else:
            avg_daily_burn = 350.0  # Standard Indian household average daily consumption
            confidence = 0.85

        days_left = max(1, int(current_net_gas / avg_daily_burn))
        now = datetime.now(timezone.utc)
        predicted_empty_date = now + timedelta(days=days_left)

        prediction_in = RefillPredictionCreate(
            device_id=device_id,
            predicted_empty_date=predicted_empty_date,
            days_left=days_left,
            confidence=round(confidence, 2)
        )
        return self.create_prediction(db, pred_in=prediction_in)


refill_service = RefillService()

