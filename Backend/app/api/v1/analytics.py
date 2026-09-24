from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.device import Device
from app.services.analytics_service import analytics_service
from app.schemas.analytics import (
    DailyConsumptionResponse,
    WeeklyConsumptionResponse,
    MonthlyConsumptionResponse,
    AverageConsumptionResponse,
    UsagePatternResponse,
    PeakUsageResponse,
    ConsumptionTrendResponse,
    LeakSummaryResponse,
    EfficiencyScoreResponse,
    AnalyticsSummary,
)

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"]
)


def _assert_device_owner(db: Session, device_id: str, current_user: User) -> Device:
    """Verify that the requested device exists and belongs to the authenticated user."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device '{device_id}' not found."
        )
    if device.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this device's analytics."
        )
    return device


@router.get("/daily-consumption", response_model=DailyConsumptionResponse)
def get_daily_consumption(
    device_id: str = Query(..., description="Target device ID"),
    days: int = Query(30, ge=1, le=180, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Calculate daily LPG consumption from consecutive weight reading drops."""
    _assert_device_owner(db, device_id, current_user)
    return analytics_service.get_daily_consumption(db, device_id=device_id, days=days)


@router.get("/weekly-consumption", response_model=WeeklyConsumptionResponse)
def get_weekly_consumption(
    device_id: str = Query(..., description="Target device ID"),
    weeks: int = Query(4, ge=1, le=26, description="Number of weeks to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Calculate weekly LPG consumption time-series and daily rollups."""
    _assert_device_owner(db, device_id, current_user)
    return analytics_service.get_weekly_consumption(db, device_id=device_id, weeks=weeks)


@router.get("/monthly-consumption", response_model=MonthlyConsumptionResponse)
def get_monthly_consumption(
    device_id: str = Query(..., description="Target device ID"),
    months: int = Query(6, ge=1, le=24, description="Number of months to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Calculate monthly aggregated LPG consumption."""
    _assert_device_owner(db, device_id, current_user)
    return analytics_service.get_monthly_consumption(db, device_id=device_id, months=months)


@router.get("/average-consumption", response_model=AverageConsumptionResponse)
def get_average_consumption(
    device_id: str = Query(..., description="Target device ID"),
    days: int = Query(30, ge=1, le=180),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Calculate average daily and weekly LPG consumption rates."""
    _assert_device_owner(db, device_id, current_user)
    return analytics_service.get_average_consumption(db, device_id=device_id, days=days)


@router.get("/usage-pattern", response_model=UsagePatternResponse)
def get_usage_pattern(
    device_id: str = Query(..., description="Target device ID"),
    days: int = Query(30, ge=1, le=180),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Analyze time-of-day LPG usage pattern (Morning, Afternoon, Evening, Night)."""
    _assert_device_owner(db, device_id, current_user)
    return analytics_service.get_usage_pattern(db, device_id=device_id, days=days)


@router.get("/peak-usage", response_model=PeakUsageResponse)
def get_peak_usage(
    device_id: str = Query(..., description="Target device ID"),
    days: int = Query(30, ge=1, le=180),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Identify highest consumption day, peak period slot, and max single drop."""
    _assert_device_owner(db, device_id, current_user)
    return analytics_service.get_peak_usage(db, device_id=device_id, days=days)


@router.get("/trend", response_model=ConsumptionTrendResponse)
def get_consumption_trend(
    device_id: str = Query(..., description="Target device ID"),
    period_days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Determine whether gas consumption is increasing, decreasing, or stable."""
    _assert_device_owner(db, device_id, current_user)
    return analytics_service.get_consumption_trend(db, device_id=device_id, period_days=period_days)


@router.get("/leak-events", response_model=LeakSummaryResponse)
def get_leak_events(
    device_id: str = Query(..., description="Target device ID"),
    days: int = Query(30, ge=1, le=180),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve leak event history, auto-shutoffs count, and peak PPM."""
    _assert_device_owner(db, device_id, current_user)
    return analytics_service.get_leak_summary(db, device_id=device_id, days=days)


@router.get("/efficiency", response_model=EfficiencyScoreResponse)
def get_efficiency_score(
    device_id: str = Query(..., description="Target device ID"),
    days: int = Query(30, ge=1, le=180),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Calculate rule-based kitchen LPG efficiency score (0–100) and grade."""
    _assert_device_owner(db, device_id, current_user)
    return analytics_service.get_efficiency_score(db, device_id=device_id, days=days)


@router.get("/summary", response_model=AnalyticsSummary)
def get_analytics_summary(
    device_id: str = Query(..., description="Target device ID"),
    days: int = Query(30, ge=1, le=180),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Fetch comprehensive analytics payload in a single API request."""
    _assert_device_owner(db, device_id, current_user)
    return analytics_service.get_full_summary(db, device_id=device_id, days=days)