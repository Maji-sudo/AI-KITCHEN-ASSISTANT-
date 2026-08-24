from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.telemetry import (
    GasReadingCreate, GasReadingResponse,
    WeightReadingCreate, WeightReadingResponse,
    LeakEventCreate, LeakEventResponse,
)
from app.services.telemetry_service import telemetry_service

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


# --- Gas Readings ---
@router.post("/gas", response_model=GasReadingResponse, status_code=status.HTTP_201_CREATED)
def record_gas_reading(
    body: GasReadingCreate,
    db: Session = Depends(get_db),
):
    """Ingest a gas sensor reading from the device (no auth required for IoT)."""
    return telemetry_service.record_gas_reading(db, reading_in=body)


@router.get("/gas/{device_id}", response_model=List[GasReadingResponse])
def get_gas_readings(
    device_id: str,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return telemetry_service.get_recent_gas_readings(db, device_id=device_id, limit=limit)


# --- Weight Readings ---
@router.post("/weight", response_model=WeightReadingResponse, status_code=status.HTTP_201_CREATED)
def record_weight_reading(
    body: WeightReadingCreate,
    db: Session = Depends(get_db),
):
    """Ingest a weight sensor reading from the device (no auth required for IoT)."""
    return telemetry_service.record_weight_reading(db, reading_in=body)


@router.get("/weight/{device_id}", response_model=List[WeightReadingResponse])
def get_weight_readings(
    device_id: str,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return telemetry_service.get_recent_weight_readings(db, device_id=device_id, limit=limit)


# --- Leak Events ---
@router.post("/leaks", response_model=LeakEventResponse, status_code=status.HTTP_201_CREATED)
def record_leak_event(
    body: LeakEventCreate,
    db: Session = Depends(get_db),
):
    """Record a new leak event detected by the device."""
    return telemetry_service.record_leak_event(db, event_in=body)


@router.get("/leaks/{device_id}", response_model=List[LeakEventResponse])
def get_unresolved_leaks(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return telemetry_service.get_unresolved_leaks(db, device_id=device_id)


@router.patch("/leaks/{event_id}/resolve", response_model=LeakEventResponse)
def resolve_leak(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = telemetry_service.resolve_leak_event(db, event_id=event_id)
    if not result:
        raise HTTPException(status_code=404, detail="Leak event not found")
    return result
