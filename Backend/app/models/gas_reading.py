import datetime
from sqlalchemy import ForeignKey, DateTime, Float, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

class GasReading(Base):
    __tablename__ = "gas_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    ppm_value: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="IOT")

    # Relationships
    device: Mapped["Device"] = relationship("Device", back_populates="gas_readings")
