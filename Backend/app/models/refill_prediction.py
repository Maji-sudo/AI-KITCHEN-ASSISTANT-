import datetime
from sqlalchemy import ForeignKey, DateTime, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class RefillPrediction(Base):
    __tablename__ = "refill_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    predicted_empty_date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    days_left: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    computed_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    # Relationships
    device: Mapped["Device"] = relationship("Device", back_populates="refill_predictions")
