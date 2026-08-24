import datetime
from sqlalchemy import ForeignKey, DateTime, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    booking_date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    distributor: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending | confirmed | delivered | cancelled
    source: Mapped[str] = mapped_column(String(50), default="app")  # app | manual | auto

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="bookings")
    device: Mapped["Device"] = relationship("Device", back_populates="bookings")
