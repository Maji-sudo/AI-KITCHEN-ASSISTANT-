import datetime
from sqlalchemy import ForeignKey, DateTime, String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class SystemLog(Base):
    __tablename__ = "system_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    log_level: Mapped[str] = mapped_column(String(20), nullable=False)  # DEBUG | INFO | WARNING | ERROR | CRITICAL
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        index=True
    )

    # Relationships
    device: Mapped["Device"] = relationship("Device", back_populates="system_logs")
