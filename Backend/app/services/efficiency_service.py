from typing import List
from sqlalchemy.orm import Session
from app.repositories.efficiency_repository import efficiency_score_repo, usage_analytics_repo
from app.schemas.efficiency import EfficiencyScoreCreate
from app.schemas.analytics import UsageAnalyticsCreate
from app.models.efficiency_score import EfficiencyScore
from app.models.usage_analytics import UsageAnalytics

class EfficiencyService:
    # --- Efficiency Score ---
    def compute_efficiency_score(self, db: Session, score_in: EfficiencyScoreCreate) -> EfficiencyScore:
        # TODO: Add logic to aggregate cooking history, leak events, and gas usage
        return efficiency_score_repo.create(db, obj_in=score_in)

    def get_latest_efficiency_scores(self, db: Session, device_id: str, limit: int = 10) -> List[EfficiencyScore]:
        return efficiency_score_repo.get_latest_for_device(db, device_id=device_id, limit=limit)

    # --- Usage Analytics ---
    def generate_usage_analytics(self, db: Session, analytics_in: UsageAnalyticsCreate) -> UsageAnalytics:
        return usage_analytics_repo.create(db, obj_in=analytics_in)

    def get_latest_usage_analytics(self, db: Session, device_id: str, limit: int = 10) -> List[UsageAnalytics]:
        return usage_analytics_repo.get_latest_for_device(db, device_id=device_id, limit=limit)

efficiency_service = EfficiencyService()
