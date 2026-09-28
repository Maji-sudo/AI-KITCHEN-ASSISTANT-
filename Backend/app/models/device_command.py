import datetime
from sqlalchemy import ForeignKey, DateTime, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class DeviceCommand(Base):
    __tablename__ = "device_commands"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    command: Mapped[str] = mapped_column(String(50), nullable=False)  # EMERGENCY_CLOSE, RESET
    status: Mapped[str] = mapped_column(String(50), default="RECORDED")  # RECORDED (software-only for now)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        index=True
    )
    executed_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True) # for future IoT

    # Relationships
    device: Mapped["Device"] = relationship("Device")
