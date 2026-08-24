from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_user
from app.models.user import User

from app.schemas.analytics import (
    UsageAnalyticsCreate,
    UsageAnalyticsResponse,
    AnalyticsSummary,
)

from app.services.analytics_service import analytics_service


router = APIRouter(
    prefix="/analytics",
    tags=["analytics"]
)


# ==========================================================
# GET DEVICE ANALYTICS
# ==========================================================

@router.get(
    "/{device_id}",
    response_model=List[UsageAnalyticsResponse]
)
def get_device_analytics(
    device_id: str,
    period_type: str = "daily",
    limit: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get historical analytics for a device.

    Example:
    GET /api/v1/analytics/ESP32-001?period_type=daily&limit=30
    """

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 100"
        )

    if period_type not in ["daily", "weekly", "monthly"]:
        raise HTTPException(
            status_code=400,
            detail="period_type must be daily, weekly, or monthly"
        )

    return analytics_service.get_device_analytics(
        db,
        device_id=device_id,
        period_type=period_type,
        limit=limit,
    )


# ==========================================================
# GET ANALYTICS SUMMARY
# ==========================================================

@router.get(
    "/{device_id}/summary",
    response_model=AnalyticsSummary
)
def get_analytics_summary(
    device_id: str,
    period_type: str = "daily",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get aggregated analytics summary for a device.
    """

    if period_type not in ["daily", "weekly", "monthly"]:
        raise HTTPException(
            status_code=400,
            detail="period_type must be daily, weekly, or monthly"
        )

    return analytics_service.get_summary(
        db,
        device_id=device_id,
        period_type=period_type,
    )


# ==========================================================
# CALCULATE ANALYTICS FOR A PERIOD
# ==========================================================

@router.post(
    "/{device_id}/calculate",
    response_model=UsageAnalyticsResponse,
    status_code=status.HTTP_201_CREATED
)
def calculate_analytics(
    device_id: str,
    start_time: datetime,
    end_time: datetime,
    period_type: str = "daily",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Calculate analytics from weight readings and save the result.

    Pipeline:

        Weight readings
              ↓
        Consumption
              ↓
        Average rate
              ↓
        Anomaly detection
              ↓
        Forecast
              ↓
        Save analytics
    """

    if end_time <= start_time:
        raise HTTPException(
            status_code=400,
            detail="end_time must be after start_time"
        )

    if period_type not in ["daily", "weekly", "monthly"]:
        raise HTTPException(
            status_code=400,
            detail="period_type must be daily, weekly, or monthly"
        )

    result = analytics_service.calculate_and_record_usage(
        db,
        device_id=device_id,
        start_time=start_time,
        end_time=end_time,
        period_type=period_type,
    )

    return result


# ==========================================================
# RECORD ANALYTICS MANUALLY
# ==========================================================

@router.post(
    "/usage",
    response_model=UsageAnalyticsResponse,
    status_code=status.HTTP_201_CREATED
)
def record_usage(
    body: UsageAnalyticsCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Save an analytics record directly.
    """

    if body.period_type not in ["daily", "weekly", "monthly"]:
        raise HTTPException(
            status_code=400,
            detail="period_type must be daily, weekly, or monthly"
        )

    return analytics_service.record_usage(
        db,
        analytics_in=body
    )