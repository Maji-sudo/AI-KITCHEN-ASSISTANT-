import datetime
from typing import Optional
from sqlalchemy import ForeignKey, DateTime, Float, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class LeakEvent(Base):
    __tablename__ = "leak_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    start_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    peak_ppm: Mapped[float] = mapped_column(Float, nullable=False)
    auto_shutoff_triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    false_alarm: Mapped[bool] = mapped_column(Boolean, default=False)
    notification_id: Mapped[Optional[int]] = mapped_column(ForeignKey("notifications.id"), nullable=True)

    # Relationships
    device: Mapped["Device"] = relationship("Device", back_populates="leak_events")
    notification: Mapped["Notification"] = relationship("Notification", backref="leak_event", uselist=False)
