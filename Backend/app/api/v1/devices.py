from typing import List

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
# DELETE / UNPAIR DEVICE
# --------------------------------------------------

@router.delete(
    "/{device_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_device(
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

    device_service.remove_device(db, device_id=device_id)
    return None