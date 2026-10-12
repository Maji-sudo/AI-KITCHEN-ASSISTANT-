from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.booking import Booking


class BookingRepository:

    @staticmethod
    def create(db: Session, booking: Booking) -> Booking:
        db.add(booking)
        db.commit()
        db.refresh(booking)
        return booking

    @staticmethod
    def get_by_id(db: Session, booking_id: int) -> Optional[Booking]:
        return (
            db.query(Booking)
            .filter(Booking.id == booking_id)
            .first()
        )

    @staticmethod
    def get_all(db: Session) -> List[Booking]:
        return (
            db.query(Booking)
            .order_by(Booking.booking_date.desc())
            .all()
        )

    @staticmethod
    def get_by_user(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Booking]:
        return (
            db.query(Booking)
            .filter(Booking.user_id == user_id)
            .order_by(Booking.booking_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_by_device(db: Session, device_id: str) -> List[Booking]:
        return (
            db.query(Booking)
            .filter(Booking.device_id == device_id)
            .order_by(Booking.booking_date.desc())
            .all()
        )

    @staticmethod
    def update_status(
        db: Session,
        booking: Booking,
        status: str,
    ) -> Booking:
        booking.status = status
        db.commit()
        db.refresh(booking)
        return booking

    @staticmethod
    def delete(db: Session, booking: Booking) -> None:
        db.delete(booking)
        db.commit()


booking_repo = BookingRepository()
