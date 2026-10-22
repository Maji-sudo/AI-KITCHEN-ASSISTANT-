import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    language_pref: Mapped[str] = mapped_column(String(10), default="en")
    delivery_address: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    notification_preferences: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    safety_preferences: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    # Relationships
    devices: Mapped[List["Device"]] = relationship("Device", back_populates="user", cascade="all, delete-orphan")
    bookings: Mapped[List["Booking"]] = relationship("Booking", back_populates="user", cascade="all, delete-orphan")
    cooking_history: Mapped[List["CookingHistory"]] = relationship("CookingHistory", back_populates="user", cascade="all, delete-orphan")
    recommendations: Mapped[List["Recommendation"]] = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")
    notifications: Mapped[List["Notification"]] = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
