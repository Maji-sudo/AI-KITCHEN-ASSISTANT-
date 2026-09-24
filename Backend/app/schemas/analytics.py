from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field


# ==========================================================
# LEGACY USAGE ANALYTICS SCHEMAS
# ==========================================================

class UsageAnalyticsBase(BaseModel):
    period_type: str
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
# DAILY CONSUMPTION SCHEMAS
# ==========================================================

class DailyConsumptionItem(BaseModel):
    date: str  # YYYY-MM-DD
    consumption_g: float
    consumption_kg: float
    reading_count: int


class DailyConsumptionResponse(BaseModel):
    device_id: str
    days: int
    total_consumption_g: float
    total_consumption_kg: float
    avg_daily_g: float
    avg_daily_kg: float
    records: List[DailyConsumptionItem] = Field(default_factory=list)


# ==========================================================
# WEEKLY CONSUMPTION SCHEMAS
# ==========================================================

class WeeklyConsumptionItem(BaseModel):
    week_label: str  # e.g., "Week 34 (Aug 18 - Aug 24)"
    start_date: str
    end_date: str
    total_consumption_g: float
    total_consumption_kg: float
    daily_avg_g: float
    daily_records: List[DailyConsumptionItem] = Field(default_factory=list)


class WeeklyConsumptionResponse(BaseModel):
    device_id: str
    weeks: int
    total_consumption_g: float
    total_consumption_kg: float
    records: List[WeeklyConsumptionItem] = Field(default_factory=list)


# ==========================================================
# MONTHLY CONSUMPTION SCHEMAS
# ==========================================================

class MonthlyConsumptionItem(BaseModel):
    month_label: str  # e.g., "August 2026"
    year: int
    month: int
    total_consumption_g: float
    total_consumption_kg: float
    daily_avg_g: float


class MonthlyConsumptionResponse(BaseModel):
    device_id: str
    months: int
    total_consumption_g: float
    total_consumption_kg: float
    records: List[MonthlyConsumptionItem] = Field(default_factory=list)


# ==========================================================
# AVERAGE CONSUMPTION SCHEMA
# ==========================================================

class AverageConsumptionResponse(BaseModel):
    device_id: str
    avg_daily_g: float
    avg_daily_kg: float
    avg_weekly_g: float
    avg_weekly_kg: float
    total_days_analyzed: int


# ==========================================================
# USAGE PATTERN SCHEMAS
# ==========================================================

class UsagePatternSlot(BaseModel):
    slot_name: str  # Morning | Afternoon | Evening | Night
    time_range: str  # e.g., "05:00 - 11:59"
    consumption_g: float
    consumption_kg: float
    percentage: float
    drop_events_count: int


class UsagePatternResponse(BaseModel):
    device_id: str
    peak_period: str
    slots: List[UsagePatternSlot] = Field(default_factory=list)
    total_consumption_g: float


# ==========================================================
# PEAK USAGE SCHEMA
# ==========================================================

class PeakUsageResponse(BaseModel):
    device_id: str
    highest_day_date: Optional[str] = None
    highest_day_consumption_g: float = 0.0
    highest_day_consumption_kg: float = 0.0
    peak_period: str = "N/A"
    max_single_drop_g: float = 0.0


# ==========================================================
# CONSUMPTION TREND SCHEMA
# ==========================================================

class ConsumptionTrendResponse(BaseModel):
    device_id: str
    trend: str  # increasing | decreasing | stable
    percent_change: float
    recent_period_avg_g: float
    prior_period_avg_g: float
    description: str


# ==========================================================
# LEAK SUMMARY SCHEMAS
# ==========================================================

class LeakEventItem(BaseModel):
    id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    peak_ppm: float
    auto_shutoff_triggered: bool
    false_alarm: bool


class LeakSummaryResponse(BaseModel):
    device_id: str
    total_leaks: int
    auto_shutoffs_triggered: int
    peak_ppm: float
    recent_events: List[LeakEventItem] = Field(default_factory=list)


# ==========================================================
# EFFICIENCY SCORE SCHEMA
# ==========================================================

class EfficiencyScoreResponse(BaseModel):
    device_id: str
    overall_score: float  # 0 to 100
    grade: str  # A | B | C | D
    explanation: str
    components_json: Dict[str, Any] = Field(default_factory=dict)


# ==========================================================
# COMPREHENSIVE ANALYTICS SUMMARY SCHEMA
# ==========================================================

class AnalyticsSummary(BaseModel):
    device_id: str
    period_days: int
    daily: DailyConsumptionResponse
    averages: AverageConsumptionResponse
    usage_pattern: UsagePatternResponse
    peak_usage: PeakUsageResponse
    trend: ConsumptionTrendResponse
    leak_summary: LeakSummaryResponse
    efficiency: EfficiencyScoreResponse