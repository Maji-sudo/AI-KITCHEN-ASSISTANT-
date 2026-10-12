import datetime
from typing import List, Optional
from sqlalchemy import String, ForeignKey, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

class Device(Base):
    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    firmware_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="inactive")
    paired_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Safety and Diagnostics
    valve_status: Mapped[str] = mapped_column(String(20), default="OPEN")
    battery_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    signal_strength: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sensor_health_status: Mapped[str] = mapped_column(String(50), default="healthy")
    last_calibrated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="devices")
    cylinders: Mapped[List["Cylinder"]] = relationship("Cylinder", back_populates="device", cascade="all, delete-orphan")
    gas_readings: Mapped[List["GasReading"]] = relationship("GasReading", back_populates="device", cascade="all, delete-orphan")
    weight_readings: Mapped[List["WeightReading"]] = relationship("WeightReading", back_populates="device", cascade="all, delete-orphan")
    leak_events: Mapped[List["LeakEvent"]] = relationship("LeakEvent", back_populates="device", cascade="all, delete-orphan")
    usage_analytics: Mapped[List["UsageAnalytics"]] = relationship("UsageAnalytics", back_populates="device", cascade="all, delete-orphan")
    refill_predictions: Mapped[List["RefillPrediction"]] = relationship("RefillPrediction", back_populates="device", cascade="all, delete-orphan")
    cooking_history: Mapped[List["CookingHistory"]] = relationship("CookingHistory", back_populates="device", cascade="all, delete-orphan")
    recommendations: Mapped[List["Recommendation"]] = relationship("Recommendation", back_populates="device", cascade="all, delete-orphan")
    efficiency_scores: Mapped[List["EfficiencyScore"]] = relationship("EfficiencyScore", back_populates="device", cascade="all, delete-orphan")
    bookings: Mapped[List["Booking"]] = relationship("Booking", back_populates="device", cascade="all, delete-orphan")
    system_logs: Mapped[List["SystemLog"]] = relationship("SystemLog", back_populates="device", cascade="all, delete-orphan")
