from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.booking_repository import booking_repo
from app.schemas.booking import BookingCreate, BookingUpdate
from app.models.booking import Booking

class BookingService:
    def create_booking(self, db: Session, booking_in: BookingCreate) -> Booking:
        return booking_repo.create(db, obj_in=booking_in)

    def update_booking_status(self, db: Session, booking_id: int, status: str) -> Optional[Booking]:
        booking = booking_repo.get(db, id=booking_id)
        if booking:
            return booking_repo.update(db, db_obj=booking, obj_in=BookingUpdate(status=status))
        return None

    def get_user_bookings(self, db: Session, user_id: int, skip: int = 0, limit: int = 50) -> List[Booking]:
        return booking_repo.get_by_user(db, user_id=user_id, skip=skip, limit=limit)

    def get_device_bookings(self, db: Session, device_id: str, skip: int = 0, limit: int = 50) -> List[Booking]:
        return booking_repo.get_by_device(db, device_id=device_id, skip=skip, limit=limit)

booking_service = BookingService()
