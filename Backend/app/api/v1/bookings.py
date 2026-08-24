from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingUpdate, BookingResponse
from app.services.booking_service import booking_service

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("/", response_model=List[BookingResponse])
def get_my_bookings(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return booking_service.get_user_bookings(db, user_id=current_user.id, skip=skip, limit=limit)


@router.post("/", response_model=BookingResponse, status_code=201)
def create_booking(
    body: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    body.user_id = current_user.id
    return booking_service.create_booking(db, booking_in=body)


@router.patch("/{booking_id}/status", response_model=BookingResponse)
def update_booking_status(
    booking_id: int,
    status: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = booking_service.update_booking_status(db, booking_id=booking_id, status=status)
    if not result:
        raise HTTPException(status_code=404, detail="Booking not found")
    return result
