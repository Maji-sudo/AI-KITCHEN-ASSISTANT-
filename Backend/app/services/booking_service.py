from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.booking_repository import booking_repo
from app.schemas.booking import BookingCreate, BookingUpdate
from app.models.booking import Booking

class BookingService:
    def create_booking(self, db: Session, booking_in: BookingCreate) -> Booking:
        booking_obj = Booking(
            user_id=booking_in.user_id,
            device_id=booking_in.device_id,
            booking_date=booking_in.booking_date,
            distributor=booking_in.distributor,
            status=booking_in.status,
            source=booking_in.source,
        )
        return booking_repo.create(db, booking=booking_obj)

    def update_booking_status(self, db: Session, booking_id: int, status: str) -> Optional[Booking]:
        booking = booking_repo.get_by_id(db, booking_id=booking_id)
        if booking:
            return booking_repo.update_status(db, booking=booking, status=status)
        return None

    def get_user_bookings(self, db: Session, user_id: int, skip: int = 0, limit: int = 50) -> List[Booking]:
        return booking_repo.get_by_user(db, user_id=user_id)

    def get_device_bookings(self, db: Session, device_id: str, skip: int = 0, limit: int = 50) -> List[Booking]:
        return booking_repo.get_by_device(db, device_id=device_id)

booking_service = BookingService()
