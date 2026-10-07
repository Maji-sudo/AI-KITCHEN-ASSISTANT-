from typing import List, Optional
from sqlalchemy.orm import Session

from app.repositories.booking_repository import booking_repo
from app.schemas.booking import BookingCreate
from app.models.booking import Booking


class BookingService:

    def create_booking(
        self,
        db: Session,
        booking_in: BookingCreate
    ) -> Booking:
        booking = Booking(**booking_in.model_dump())
        return booking_repo.create(db, booking=booking)

    def update_booking_status(
        self,
        db: Session,
        booking_id: int,
        status: str
    ) -> Optional[Booking]:

        booking = booking_repo.get_by_id(
            db,
            booking_id=booking_id
        )

        if booking:
            return booking_repo.update_status(
                db,
                booking=booking,
                status=status
            )

        return None

    def get_user_bookings(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[Booking]:

        return booking_repo.get_by_user(
            db,
            user_id=user_id,
            skip=skip,
            limit=limit
        )

    def get_device_bookings(
        self,
        db: Session,
        device_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Booking]:

        bookings = booking_repo.get_by_device(
            db,
            device_id=device_id
        )

        return bookings[skip:skip + limit]


booking_service = BookingService()