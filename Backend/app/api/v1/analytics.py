from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.device import Device

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


# ─── helpers ──────────────────────────────────────────────────────────────────

def _assert_device_owner(db: Session, device_id: str, current_user: User) -> Device:
    device = db.query(Device).filter(Device.id == device_id).first()
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    if device.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this device")
    return device


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
    """Get historical analytics for a device owned by the current user."""

    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")

    if period_type not in ["daily", "weekly", "monthly"]:
        raise HTTPException(status_code=400, detail="period_type must be daily, weekly, or monthly")

    _assert_device_owner(db, device_id, current_user)

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
    """Get aggregated analytics summary for a device owned by the current user."""

    if period_type not in ["daily", "weekly", "monthly"]:
        raise HTTPException(status_code=400, detail="period_type must be daily, weekly, or monthly")

    _assert_device_owner(db, device_id, current_user)

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
    if end_time <= start_time:
        raise HTTPException(status_code=400, detail="end_time must be after start_time")

    if period_type not in ["daily", "weekly", "monthly"]:
        raise HTTPException(status_code=400, detail="period_type must be daily, weekly, or monthly")

    _assert_device_owner(db, device_id, current_user)

    return analytics_service.calculate_and_record_usage(
        db,
        device_id=device_id,
        start_time=start_time,
        end_time=end_time,
        period_type=period_type,
    )


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
    if body.period_type not in ["daily", "weekly", "monthly"]:
        raise HTTPException(status_code=400, detail="period_type must be daily, weekly, or monthly")

    # Verify device ownership for manually recorded analytics too
    _assert_device_owner(db, body.device_id, current_user)

    return analytics_service.record_usage(
        db,
        analytics_in=body
    )