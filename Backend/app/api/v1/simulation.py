from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.device import Device
from app.schemas.simulation import (
    SimulateDeviceRequest,
    SimulateDataRequest,
    SimulateSafetyRequest,
    ResetDataRequest,
    ManualCookingRequest,
    SimulationResponse,
)
from app.schemas.device import DeviceResponse
from app.schemas.cooking import CookingHistoryCreate, CookingHistoryResponse
from app.services.simulation_service import simulation_service
from app.services.cooking_service import cooking_service

router = APIRouter(prefix="/simulation", tags=["simulation"])


def _assert_debug_enabled():
    """Safety guard: ensure simulation functionality is strictly restricted to DEBUG mode."""
    if not settings.DEBUG:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Simulation controls are only available in development/debug mode"
        )


def _assert_device_owner(db: Session, device_id: str, current_user: User) -> Device:
    device = db.query(Device).filter(Device.id == device_id).first()
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    if device.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this device")
    return device


@router.post("/device", response_model=DeviceResponse)
def create_simulated_device(
    body: SimulateDeviceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new simulated device for the authenticated user.
    Available only in development mode.
    """
    _assert_debug_enabled()
    device = simulation_service.create_simulated_device(
        db,
        user_id=current_user.id,
        name=body.name or "Kitchen SafeGas Hub",
        cylinder_type=body.cylinder_type or "14.2kg",
        custom_id=body.device_id
    )
    return device


@router.post("/generate", response_model=SimulationResponse)
def generate_simulated_data(
    body: SimulateDataRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate realistic multi-day cylinder weight, consumption, cooking, and gas telemetry.
    Verifies that the target device belongs to the authenticated user.
    """
    _assert_debug_enabled()
    _assert_device_owner(db, body.device_id, current_user)

    details = simulation_service.generate_usage_simulation(
        db,
        device_id=body.device_id,
        user_id=current_user.id,
        days=body.days,
        pattern=body.pattern
    )
    return SimulationResponse(
        success=True,
        message=f"Generated {body.days} days of realistic {body.pattern} usage data",
        details=details
    )


@router.post("/safety", response_model=SimulationResponse)
def trigger_safety_scenario(
    body: SimulateSafetyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Simulate a gas safety scenario (normal, warning, critical).
    Verifies that the target device belongs to the authenticated user.
    """
    _assert_debug_enabled()
    _assert_device_owner(db, body.device_id, current_user)

    details = simulation_service.generate_safety_scenario(
        db,
        device_id=body.device_id,
        user_id=current_user.id,
        scenario=body.scenario
    )
    return SimulationResponse(
        success=True,
        message=f"Executed {body.scenario} safety scenario",
        details=details
    )


@router.post("/reset", response_model=SimulationResponse)
def reset_simulated_data(
    body: ResetDataRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Reset simulated telemetry for a device.
    Verifies that the target device belongs to the authenticated user.
    """
    _assert_debug_enabled()
    _assert_device_owner(db, body.device_id, current_user)

    details = simulation_service.reset_simulated_data(
        db,
        device_id=body.device_id,
        user_id=current_user.id
    )
    return SimulationResponse(
        success=True,
        message="Simulated telemetry reset successfully",
        details=details
    )


@router.post("/manual/cooking", response_model=CookingHistoryResponse, status_code=status.HTTP_201_CREATED)
def manual_cooking_entry(
    body: ManualCookingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Manual cooking activity entry associated with the user and their device.
    """
    if body.device_id:
        _assert_device_owner(db, body.device_id, current_user)

    session_in = CookingHistoryCreate(
        user_id=current_user.id,
        device_id=body.device_id or "",
        dish_id=body.dish_id,
        logged_date=body.logged_date,
        actual_gas_g=body.actual_gas_g,
        actual_duration_min=body.cooking_duration_min
    )
    return cooking_service.record_cooking_session(db, session_in=session_in)
