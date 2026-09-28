from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.gas_reading import GasReading
from app.models.weight_reading import WeightReading
from app.models.leak_event import LeakEvent
from app.models.cooking_history import CookingHistory
from app.models.usage_analytics import UsageAnalytics


class AnalyticsRepository:

    def get_weight_readings_for_period(
        self,
        db: Session,
        *,
        device_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[WeightReading]:
        query = db.query(WeightReading).filter(WeightReading.device_id == device_id)
        if start_time:
            query = query.filter(WeightReading.timestamp >= start_time)
        if end_time:
            query = query.filter(WeightReading.timestamp <= end_time)
        return query.order_by(WeightReading.timestamp.asc()).all()

    def get_gas_readings_for_period(
        self,
        db: Session,
        *,
        device_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[GasReading]:
        query = db.query(GasReading).filter(GasReading.device_id == device_id)
        if start_time:
            query = query.filter(GasReading.timestamp >= start_time)
        if end_time:
            query = query.filter(GasReading.timestamp <= end_time)
        return query.order_by(GasReading.timestamp.asc()).all()

    def get_leak_events_for_period(
        self,
        db: Session,
        *,
        device_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[LeakEvent]:
        query = db.query(LeakEvent).filter(LeakEvent.device_id == device_id)
        if start_time:
            query = query.filter(LeakEvent.start_time >= start_time)
        if end_time:
            query = query.filter(LeakEvent.start_time <= end_time)
        return query.order_by(LeakEvent.start_time.desc()).all()

    def get_cooking_history_for_period(
        self,
        db: Session,
        *,
        device_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[CookingHistory]:
        query = db.query(CookingHistory).filter(CookingHistory.device_id == device_id)
        if start_time:
            query = query.filter(CookingHistory.logged_date >= start_time)
        if end_time:
            query = query.filter(CookingHistory.logged_date <= end_time)
        return query.order_by(CookingHistory.logged_date.desc()).all()

    def get_usage_analytics(
        self,
        db: Session,
        *,
        device_id: str,
        period_type: str,
        limit: int = 30
    ) -> List[UsageAnalytics]:
        return (
            db.query(UsageAnalytics)
            .filter(
                UsageAnalytics.device_id == device_id,
                UsageAnalytics.period_type == period_type
            )
            .order_by(UsageAnalytics.period_start.desc())
            .limit(limit)
            .all()
        )

    def create_usage_analytics(
        self,
        db: Session,
        *,
        analytics_obj: UsageAnalytics
    ) -> UsageAnalytics:
        db.add(analytics_obj)
        db.commit()
        db.refresh(analytics_obj)
        return analytics_obj


analytics_repo = AnalyticsRepository()