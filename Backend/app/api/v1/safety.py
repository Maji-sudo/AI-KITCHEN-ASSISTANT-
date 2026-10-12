"""
Safety API Router — Phase 1
============================

Exposes device-level safety and valve-control endpoints.

Architecture contract:
  request → router → auth/ownership dep → existing service → response

Business logic lives in:
  • SafetyReadService
  • DiagnosticsService
  • ValveCommandService

No safety logic is duplicated here.

Endpoint prefix: /devices (device-centric, consistent with devices.py)
Full paths under /api/v1/devices/{device_id}/...
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_user

from app.models.user import User
from app.schemas.safety import SafetyStatusResponse, ActiveLeakResponse, LeakHistoryResponse
from app.schemas.telemetry import GasReadingResponse
from app.schemas.diagnostics import DeviceDiagnosticsResponse
from app.schemas.device import DeviceResponse

from app.services.safety_read_service import safety_read_service
from app.services.diagnostics_service import diagnostics_service
from app.services.valve_command_service import valve_command_service
from app.services.realtime_service import realtime_manager
from app.services.jwt_service import decode_access_token
from app.api.deps import verify_device_ownership
from fastapi.responses import StreamingResponse
from fastapi import HTTPException, status
import asyncio
import json

router = APIRouter(
    prefix="/devices",
    tags=["safety"],
)

# ==============================================================
# GET /devices/{device_id}/safety/stream
# ==============================================================

@router.get(
    "/{device_id}/safety/stream",
    summary="Real-time safety update stream (SSE)",
    description="Subscribe to Server-Sent Events for real-time safety state changes.",
)
async def stream_safety_updates(
    device_id: str,
    token: str = Query(..., description="JWT access token passed via query param for EventSource"),
    db: Session = Depends(get_db),
):
    # 1. Authenticate via token query param
    payload = decode_access_token(token)
    if payload is None or payload.sub is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload.sub

    # 2. Verify device ownership
    verify_device_ownership(db, user_id=user_id, device_id=device_id)

    # 3. Setup SSE Generator
    async def event_generator():
        queue = await realtime_manager.subscribe(device_id)
        try:
            while True:
                # Wait for the next event from the queue
                event = await queue.get()
                # Yield in SSE format
                yield f"data: {json.dumps(event)}\n\n"
        except asyncio.CancelledError:
            # Client disconnected
            pass
        finally:
            realtime_manager.unsubscribe(device_id, queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")



# ==============================================================
# GET /devices/{device_id}/safety
# ==============================================================

@router.get(
    "/{device_id}/safety",
    response_model=SafetyStatusResponse,
    summary="Get current safety summary for a device",
    description=(
        "Returns the latest gas PPM, classified status (normal/warning/critical), "
        "valve state, connection status, and last-seen timestamp. "
        "Thresholds: normal < 500 PPM | warning 500–999 | critical ≥ 1000."
    ),
)
def get_device_safety(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SafetyStatusResponse:
    """
    Return the current safety status for the authenticated user's device.

    Raises:
      401 – unauthenticated
      403 – device belongs to a different user
      404 – device does not exist
    """
    return safety_read_service.get_current_safety(
        db,
        device_id=device_id,
        user_id=current_user.id,
    )


# ==============================================================
# GET /devices/{device_id}/gas-readings
# ==============================================================

@router.get(
    "/{device_id}/gas-readings",
    response_model=List[GasReadingResponse],
    summary="Get recent gas readings for a device",
    description=(
        "Returns up to `limit` recent gas readings ordered ascending by timestamp. "
        "Optionally filter with `start` / `end` ISO-8601 datetime query params."
    ),
)
def get_device_gas_readings(
    device_id: str,
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum readings to return"),
    start: Optional[datetime] = Query(default=None, description="Filter readings after this ISO-8601 timestamp"),
    end: Optional[datetime] = Query(default=None, description="Filter readings before this ISO-8601 timestamp"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[GasReadingResponse]:
    """
    Return recent gas readings for the device.

    Raises:
      401 – unauthenticated
      403 – device belongs to a different user
      404 – device does not exist
    """
    return safety_read_service.get_gas_history(
        db,
        device_id=device_id,
        user_id=current_user.id,
        limit=limit,
        start=start,
        end=end,
    )


# ==============================================================
# GET /devices/{device_id}/leaks/active
# ==============================================================

@router.get(
    "/{device_id}/leaks/active",
    response_model=Optional[ActiveLeakResponse],
    summary="Get the currently active (unresolved) leak event",
    description=(
        "Returns the single active leak event if one exists, or null if the device "
        "is currently in a safe state."
    ),
)
def get_active_leak(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Optional[ActiveLeakResponse]:
    """
    Return the active (unresolved) leak event for the device, if any.

    Raises:
      401 – unauthenticated
      403 – device belongs to a different user
      404 – device does not exist
    """
    return safety_read_service.get_active_leak(
        db,
        device_id=device_id,
        user_id=current_user.id,
    )


# ==============================================================
# GET /devices/{device_id}/leaks
# ==============================================================

@router.get(
    "/{device_id}/leaks",
    response_model=LeakHistoryResponse,
    summary="Get leak incident history for a device",
    description=(
        "Returns resolved and active leak events, ordered most-recent first. "
        "Use the `limit` query parameter to cap the number of results (max 1000)."
    ),
)
def get_leak_history(
    device_id: str,
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum leak events to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LeakHistoryResponse:
    """
    Return the full leak event history for the device.

    Raises:
      401 – unauthenticated
      403 – device belongs to a different user
      404 – device does not exist
    """
    return safety_read_service.get_leak_history(
        db,
        device_id=device_id,
        user_id=current_user.id,
        limit=limit,
    )


# ==============================================================
# GET /devices/{device_id}/diagnostics
# ==============================================================

@router.get(
    "/{device_id}/diagnostics",
    response_model=DeviceDiagnosticsResponse,
    summary="Get device diagnostics",
    description=(
        "Returns a structured diagnostics report including device identity, "
        "connection status, sensor health, latest telemetry snapshot, "
        "and valve safety state."
    ),
)
def get_device_diagnostics(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeviceDiagnosticsResponse:
    """
    Return the full diagnostics report for the device.

    Raises:
      401 – unauthenticated
      403 – device belongs to a different user
      404 – device does not exist
    """
    return diagnostics_service.get_diagnostics(
        db,
        device_id=device_id,
        user_id=current_user.id,
    )


# ==============================================================
# POST /devices/{device_id}/valve/emergency-close
# ==============================================================

@router.post(
    "/{device_id}/valve/emergency-close",
    response_model=DeviceResponse,
    summary="Trigger emergency valve close",
    description=(
        "Issues an emergency-close command for the device's gas valve. "
        "Idempotent: if the valve is already CLOSED, the command is skipped and "
        "the current device state is returned unchanged. "
        "Creates a DeviceCommand record with command='EMERGENCY_CLOSE'."
    ),
)
def emergency_close_valve(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeviceResponse:
    """
    Emergency-close the valve for the authenticated user's device.

    Idempotency:
      - If valve is already CLOSED: returns current device state; no new command written.
      - If valve is OPEN: sets valve_status = 'CLOSED', writes DeviceCommand record.

    Raises:
      401 – unauthenticated
      403 – device belongs to a different user
      404 – device does not exist
    """
    return valve_command_service.emergency_close(
        db,
        device_id=device_id,
        user_id=current_user.id,
    )


# ==============================================================
# POST /devices/{device_id}/valve/reset
# ==============================================================

@router.post(
    "/{device_id}/valve/reset",
    response_model=DeviceResponse,
    summary="Manually reset (reopen) the valve",
    description=(
        "Manually reopens the gas valve after emergency closure. "
        "Idempotent: if the valve is already OPEN, returns current state unchanged. "
        "Does NOT auto-reopen based on PPM levels — explicit manual action required. "
        "Creates a DeviceCommand record with command='RESET'."
    ),
)
def reset_valve(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeviceResponse:
    """
    Manually reset (reopen) the valve for the authenticated user's device.

    Safety lockout preserved:
      - Valve does NOT auto-reopen when PPM normalises.
      - This endpoint requires explicit user action.

    Idempotency:
      - If valve is already OPEN: returns current device state; no new command written.
      - If valve is CLOSED: sets valve_status = 'OPEN', writes DeviceCommand record.

    Raises:
      401 – unauthenticated
      403 – device belongs to a different user
      404 – device does not exist
    """
    return valve_command_service.reset_valve(
        db,
        device_id=device_id,
        user_id=current_user.id,
    )
