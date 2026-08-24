from typing import List
from sqlalchemy.orm import Session
from app.repositories.base_repository import CRUDBase
from app.models.efficiency_score import EfficiencyScore
from app.models.usage_analytics import UsageAnalytics
from app.schemas.efficiency import EfficiencyScoreCreate
from app.schemas.analytics import UsageAnalyticsCreate
from pydantic import BaseModel

class EfficiencyScoreRepository(CRUDBase[EfficiencyScore, EfficiencyScoreCreate, BaseModel]):
    def get_latest_for_device(self, db: Session, *, device_id: str, limit: int = 10) -> List[EfficiencyScore]:
        return (
            db.query(EfficiencyScore)
            .filter(EfficiencyScore.device_id == device_id)
            .order_by(EfficiencyScore.computed_at.desc())
            .limit(limit)
            .all()
        )

class UsageAnalyticsRepository(CRUDBase[UsageAnalytics, UsageAnalyticsCreate, BaseModel]):
    def get_latest_for_device(self, db: Session, *, device_id: str, limit: int = 10) -> List[UsageAnalytics]:
        return (
            db.query(UsageAnalytics)
            .filter(UsageAnalytics.device_id == device_id)
            .order_by(UsageAnalytics.period_start.desc())
            .limit(limit)
            .all()
        )

    def get_by_period_type(self, db: Session, *, device_id: str, period_type: str, limit: int = 30) -> List[UsageAnalytics]:
        return (
            db.query(UsageAnalytics)
            .filter(UsageAnalytics.device_id == device_id, UsageAnalytics.period_type == period_type)
            .order_by(UsageAnalytics.period_start.desc())
            .limit(limit)
            .all()
        )

efficiency_score_repo = EfficiencyScoreRepository(EfficiencyScore)
usage_analytics_repo = UsageAnalyticsRepository(UsageAnalytics)
