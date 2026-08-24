import datetime
from sqlalchemy import String, ForeignKey, DateTime, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

class Cylinder(Base):
    __tablename__ = "cylinders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    tare_weight_g: Mapped[float] = mapped_column(Float, nullable=False)
    full_weight_g: Mapped[float] = mapped_column(Float, nullable=False)
    install_date: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )
    cylinder_type: Mapped[str] = mapped_column(String(50), default="14.2kg")

    # Relationships
    device: Mapped["Device"] = relationship("Device", back_populates="cylinders")
