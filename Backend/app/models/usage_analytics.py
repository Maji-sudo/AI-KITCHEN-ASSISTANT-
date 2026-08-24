import datetime
from typing import Optional
from sqlalchemy import ForeignKey, DateTime, Float, Boolean, String, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class UsageAnalytics(Base):
    __tablename__ = "usage_analytics"
    __table_args__ = (
        UniqueConstraint("device_id", "period_type", "period_start", name="uq_usage_analytics_device_period"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    period_type: Mapped[str] = mapped_column(String(20), nullable=False)  # daily | weekly | monthly
    period_start: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumption_g: Mapped[float] = mapped_column(Float, nullable=False)
    avg_rate: Mapped[float] = mapped_column(Float, nullable=False)
    anomaly_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    forecast_next_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    device: Mapped["Device"] = relationship("Device", back_populates="usage_analytics")
