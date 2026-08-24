from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel, Field


# ==========================================================
# USAGE ANALYTICS
# ==========================================================

class UsageAnalyticsBase(BaseModel):
    period_type: str  # daily | weekly | monthly
    period_start: datetime
    consumption_g: float
    avg_rate: float
    anomaly_flag: Optional[bool] = False
    forecast_next_g: Optional[float] = None


class UsageAnalyticsCreate(UsageAnalyticsBase):
    device_id: str


class UsageAnalyticsResponse(UsageAnalyticsBase):
    id: int
    device_id: str

    class Config:
        from_attributes = True


# ==========================================================
# ANALYTICS SUMMARY
# ==========================================================

class AnalyticsSummary(BaseModel):
    device_id: str
    period_type: str

    total_consumption_g: float
    avg_daily_rate_g: float
    anomaly_count: int

    records: List[UsageAnalyticsResponse] = Field(
        default_factory=list
    )