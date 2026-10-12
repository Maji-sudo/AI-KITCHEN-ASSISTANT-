"""
SafeGas AI — Recommendations Router
=====================================
All endpoints require a valid JWT (get_current_user).
Data is automatically scoped to the authenticated user.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.device import Device
from app.schemas.recommendation import (
    RecommendationResponse,
    GenerateRequest,
    GenerateResponse,
)
from app.services.recommendation_service import recommendation_service

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


# ---------------------------------------------------------------------------
# Helper — verify device ownership (mirrors the analytics router pattern)
# ---------------------------------------------------------------------------

def _assert_device_owner(db: Session, device_id: str, current_user: User) -> Device:
    device = db.query(Device).filter(Device.id == device_id).first()
    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device '{device_id}' not found.",
        )
    if device.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this device.",
        )
    return device


# ---------------------------------------------------------------------------
# GET /recommendations/         — list active recommendations
# ---------------------------------------------------------------------------

@router.get("/", response_model=List[RecommendationResponse])
def get_my_recommendations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    include_all: bool = Query(
        False,
        description="If true, returns all statuses (active + acted + dismissed). Default: active only.",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return recommendations for the authenticated user.
    By default only 'active' recommendations are returned, sorted by priority.
    Set include_all=true to see acted and dismissed records too.
    """
    if include_all:
        return recommendation_service.get_all_recommendations(
            db, user_id=int(current_user.id), skip=skip, limit=limit
        )
    return recommendation_service.get_active_recommendations(
        db, user_id=int(current_user.id), skip=skip, limit=limit
    )


# ---------------------------------------------------------------------------
# GET /recommendations/counts   — summary badge data
# ---------------------------------------------------------------------------

@router.get("/counts")
def get_recommendation_counts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return {active, acted, dismissed} counts for the authenticated user."""
    return recommendation_service.get_counts(db, user_id=int(current_user.id))


# ---------------------------------------------------------------------------
# POST /recommendations/generate — run the rule engine and persist results
# ---------------------------------------------------------------------------

@router.post("/generate", response_model=GenerateResponse, status_code=status.HTTP_200_OK)
def generate_recommendations(
    body: GenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Trigger the deterministic rule-based recommendation engine for a device.
    - Verifies the device belongs to the authenticated user.
    - Deletes stale 'active' recommendations for the device.
    - Evaluates 10 rules against the latest analytics + cooking history data.
    - Persists and returns the generated recommendations.
    """
    _assert_device_owner(db, body.device_id, current_user)

    try:
        return recommendation_service.generate_recommendations(
            db,
            current_user=current_user,
            device_id=body.device_id,
            days=body.days,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(exc)}",
        )


# ---------------------------------------------------------------------------
# PATCH /recommendations/{rec_id}/dismiss
# ---------------------------------------------------------------------------

@router.patch("/{rec_id}/dismiss", response_model=RecommendationResponse)
def dismiss_recommendation(
    rec_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a recommendation as dismissed. Ownership is verified server-side."""
    result = recommendation_service.dismiss_recommendation(
        db, rec_id=rec_id, user_id=int(current_user.id)
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found or does not belong to you.",
        )
    return result


# ---------------------------------------------------------------------------
# PATCH /recommendations/{rec_id}/act
# ---------------------------------------------------------------------------

@router.patch("/{rec_id}/act", response_model=RecommendationResponse)
def act_on_recommendation(
    rec_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a recommendation as acted upon (completed). Ownership is verified server-side."""
    result = recommendation_service.act_on_recommendation(
        db, rec_id=rec_id, user_id=int(current_user.id)
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found or does not belong to you.",
        )
    return result
