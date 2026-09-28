from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.device import Device
from app.schemas.refill import RefillPredictionResponse
from app.services.refill_service import refill_service

router = APIRouter(prefix="/refill", tags=["refill"])


def _assert_device_owner(db: Session, device_id: str, current_user: User) -> Device:
    device = db.query(Device).filter(Device.id == device_id).first()
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    if device.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this device")
    return device


@router.get("/{device_id}", response_model=RefillPredictionResponse)
def get_latest_prediction(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the latest refill prediction for a device. If none exists, compute one."""
    _assert_device_owner(db, device_id, current_user)
    prediction = refill_service.get_latest_prediction(db, device_id=device_id)
    if not prediction:
        prediction = refill_service.compute_refill_prediction(db, device_id=device_id)
    return prediction


@router.get("/{device_id}/history", response_model=List[RefillPredictionResponse])
def get_prediction_history(
    device_id: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get historical refill predictions for a device."""
    _assert_device_owner(db, device_id, current_user)
    return refill_service.get_prediction_history(db, device_id=device_id, limit=limit)


@router.post("/{device_id}/predict", response_model=RefillPredictionResponse)
def recompute_prediction(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trigger dynamic refill prediction calculation for a device."""
    _assert_device_owner(db, device_id, current_user)
    return refill_service.compute_refill_prediction(db, device_id=device_id)
