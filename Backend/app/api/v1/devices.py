from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_user

from app.models.user import User
from app.models.device import Device

from app.schemas.device import (
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    CylinderCreate,
    CylinderResponse,
)

from app.services.device_service import device_service
from app.schemas.safety import SafetyStatusResponse, ActiveLeakResponse, LeakHistoryResponse
from app.schemas.telemetry import GasReadingResponse
from app.services.safety_read_service import safety_read_service
from fastapi import Query




router = APIRouter(
    prefix="/devices",
    tags=["devices"]
)


# --------------------------------------------------
# GET ALL DEVICES OF CURRENT USER
# --------------------------------------------------

@router.get(
    "/",
    response_model=List[DeviceResponse]
)
def get_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return device_service.get_user_devices(
        db,
        user_id=current_user.id
    )


# --------------------------------------------------
# GET ONE DEVICE
# --------------------------------------------------

@router.get(
    "/{device_id}",
    response_model=DeviceResponse
)
def get_device(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    device = device_service.get_device(
        db,
        device_id=device_id
    )

    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    # Make sure the device belongs to the logged-in user
    if device.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this device"
        )

    return device


# --------------------------------------------------
# REGISTER / PAIR DEVICE
# --------------------------------------------------

@router.post(
    "/",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED
)
def register_device(
    device_in: DeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Force the device to belong to the logged-in user.
    device_in = device_in.model_copy(
        update={"user_id": current_user.id}
    )

    existing_device = device_service.get_device(
        db,
        device_id=device_in.id
    )

    if existing_device:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Device already exists"
        )

    return device_service.register_device(
        db,
        device_in=device_in
    )


# --------------------------------------------------
# UPDATE DEVICE
# --------------------------------------------------

@router.put(
    "/{device_id}",
    response_model=DeviceResponse
)
def update_device(
    device_id: str,
    device_in: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    device = device_service.get_device(
        db,
        device_id=device_id
    )

    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    if device.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this device"
        )

    return device_service.update_device(
        db,
        db_device=device,
        device_in=device_in
    )


# --------------------------------------------------
# GET CYLINDERS OF A DEVICE
# --------------------------------------------------

@router.get(
    "/{device_id}/cylinders",
    response_model=List[CylinderResponse]
)
def get_cylinders(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    device = device_service.get_device(
        db,
        device_id=device_id
    )

    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    if device.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this device"
        )

    return device_service.get_device_cylinders(
        db,
        device_id=device_id
    )


# --------------------------------------------------
# ADD CYLINDER TO DEVICE
# --------------------------------------------------

@router.post(
    "/{device_id}/cylinders",
    response_model=CylinderResponse,
    status_code=status.HTTP_201_CREATED
)
def add_cylinder(
    device_id: str,
    cylinder_in: CylinderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    device = device_service.get_device(
        db,
        device_id=device_id
    )

    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    if device.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this device"
        )

    # Make sure cylinder is attached to the URL device,
    # not to a different device_id sent by the client.
    cylinder_in = cylinder_in.model_copy(
        update={"device_id": device_id}
    )

    return device_service.add_cylinder(
        db,
        cylinder_in=cylinder_in
    )


# --------------------------------------------------
# VALVE CONTROL
# --------------------------------------------------

from app.services.valve_command_service import valve_command_service

@router.post(
    "/{device_id}/valve/emergency-close",
    response_model=DeviceResponse
)
def emergency_close_valve(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Manually request an emergency close for a device.
    """
    return valve_command_service.emergency_close(db, device_id, current_user.id)


@router.post(
    "/{device_id}/valve/reset",
    response_model=DeviceResponse
)
def reset_valve(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Manually request a reset to reopen the valve.
    """
    return valve_command_service.reset_valve(db, device_id, current_user.id)


# --------------------------------------------------
# DIAGNOSTICS
# --------------------------------------------------

from app.schemas.diagnostics import DeviceDiagnosticsResponse
from app.services.diagnostics_service import diagnostics_service

@router.get(
    "/{device_id}/diagnostics",
    response_model=DeviceDiagnosticsResponse
)
def get_device_diagnostics(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get backend-driven diagnostics and status readout for a device.
    """
    return diagnostics_service.get_diagnostics(db, device_id, current_user.id)

# --------------------------------------------------
# SAFETY READ ENDPOINTS (Phase 7)
# --------------------------------------------------

@router.get(
    "/{device_id}/safety",
    response_model=SafetyStatusResponse,
)
def get_device_safety(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return current safety status for a device (latest reading, valve, connection)."""
    return safety_read_service.get_current_safety(db, device_id, current_user.id)

@router.get(
    "/{device_id}/gas-readings",
    response_model=List[GasReadingResponse],
)
def get_device_gas_history(
    device_id: str,
    limit: int = Query(100, ge=1, le=1000),
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Historical gas telemetry, ordered chronologically."""
    return safety_read_service.get_gas_history(
        db, device_id, current_user.id, limit=limit, start=start, end=end
    )

@router.get(
    "/{device_id}/leaks/active",
    response_model=Optional[ActiveLeakResponse],
)
def get_active_leak(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the currently active leak event, if any."""
    return safety_read_service.get_active_leak(db, device_id, current_user.id)

@router.get(
    "/{device_id}/leaks",
    response_model=LeakHistoryResponse,
)
def get_leak_history(
    device_id: str,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return leak event history for a device, newest first."""
    return safety_read_service.get_leak_history(db, device_id, current_user.id, limit=limit)

