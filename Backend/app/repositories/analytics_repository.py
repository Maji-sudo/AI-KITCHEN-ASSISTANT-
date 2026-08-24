from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session

from app.models.gas_reading import GasReading
from app.models.weight_reading import WeightReading
from app.models.usage_analytics import UsageAnalytics


class AnalyticsRepository:

    def get_gas_readings(
        self,
        db: Session,
        *,
        device_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[GasReading]:

        return (
            db.query(GasReading)
            .filter(
                GasReading.device_id == device_id,
                GasReading.timestamp >= start_time,
                GasReading.timestamp <= end_time
            )
            .order_by(GasReading.timestamp.asc())
            .all()
        )

    def get_weight_readings(
        self,
        db: Session,
        *,
        device_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[WeightReading]:

        return (
            db.query(WeightReading)
            .filter(
                WeightReading.device_id == device_id,
                WeightReading.timestamp >= start_time,
                WeightReading.timestamp <= end_time
            )
            .order_by(WeightReading.timestamp.asc())
            .all()
        )

    def get_usage_analytics(
        self,
        db: Session,
        *,
        device_id: str,
        period_type: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[UsageAnalytics]:

        query = (
            db.query(UsageAnalytics)
            .filter(
                UsageAnalytics.device_id == device_id,
                UsageAnalytics.period_type == period_type
            )
        )

        if start_time:
            query = query.filter(
                UsageAnalytics.period_start >= start_time
            )

        if end_time:
            query = query.filter(
                UsageAnalytics.period_start <= end_time
            )

        return (
            query
            .order_by(UsageAnalytics.period_start.asc())
            .all()
        )

    def get_latest_usage_analytics(
        self,
        db: Session,
        *,
        device_id: str,
        period_type: str
    ) -> Optional[UsageAnalytics]:

        return (
            db.query(UsageAnalytics)
            .filter(
                UsageAnalytics.device_id == device_id,
                UsageAnalytics.period_type == period_type
            )
            .order_by(UsageAnalytics.period_start.desc())
            .first()
        )

    def create_usage_analytics(
        self,
        db: Session,
        *,
        device_id: str,
        period_type: str,
        period_start: datetime,
        consumption_g: float,
        avg_rate: float,
        anomaly_flag: bool,
        forecast_next_g: Optional[float]
    ) -> UsageAnalytics:

        analytics = UsageAnalytics(
            device_id=device_id,
            period_type=period_type,
            period_start=period_start,
            consumption_g=consumption_g,
            avg_rate=avg_rate,
            anomaly_flag=anomaly_flag,
            forecast_next_g=forecast_next_g
        )

        db.add(analytics)
        db.commit()
        db.refresh(analytics)

        return analytics