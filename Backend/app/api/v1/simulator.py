from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_user, verify_device_ownership
from app.models.user import User
from app.schemas.simulator import (
    SimulatorStartRequest,
    SimulatorStopRequest,
    SimulatorStatusResponse,
)
from app.services.simulator_service import simulator_service

router = APIRouter(prefix="/simulator", tags=["simulator"])


@router.post("/start", status_code=status.HTTP_200_OK)
def start_simulator(
    body: SimulatorStartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Start the realtime telemetry simulator for an owned device.
    Development mode only.
    """
    # Authenticate and enforce device ownership
    verify_device_ownership(db, current_user.id, body.device_id)

    # Delegate simulator lifecycle to service (service raises 409 if already running)
    sim_state = simulator_service.start_simulation(
        device_id=body.device_id,
        baseline_ppm=body.baseline_ppm,
        interval_seconds=body.interval_seconds,
        count=body.count,
        mode=body.mode or "fluctuate",
    )

    return {
        "message": "Simulator started successfully",
        "status": sim_state.to_dict(),
    }


@router.post("/stop", status_code=status.HTTP_200_OK)
def stop_simulator(
    body: SimulatorStopRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Stop the realtime telemetry simulator for an owned device.
    """
    verify_device_ownership(db, current_user.id, body.device_id)

    stopped = simulator_service.stop_simulation(body.device_id)
    status_dict = simulator_service.get_status(body.device_id)

    return {
        "message": "Simulator stopped" if stopped else "Simulator was not running",
        "status": status_dict,
    }


@router.get("/status/{device_id}", response_model=SimulatorStatusResponse)
def get_simulator_status_path(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get simulator status by device_id path parameter.
    """
    verify_device_ownership(db, current_user.id, device_id)
    status_dict = simulator_service.get_status(device_id)
    return SimulatorStatusResponse(**status_dict)


@router.get("/status", response_model=SimulatorStatusResponse)
def get_simulator_status_query(
    device_id: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get simulator status by device_id query parameter.
    """
    verify_device_ownership(db, current_user.id, device_id)
    status_dict = simulator_service.get_status(device_id)
    return SimulatorStatusResponse(**status_dict)
