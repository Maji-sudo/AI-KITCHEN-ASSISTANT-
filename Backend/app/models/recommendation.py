import datetime
from typing import Any, Dict, Optional
from sqlalchemy import ForeignKey, Float, String, Integer, Text, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # safety | efficiency | cooking | refill | general
    message: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_facts_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=3)  # 1=critical | 2=high | 3=medium | 4=low
    status: Mapped[str] = mapped_column(String(50), default="active")  # active | acted | dismissed
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="recommendations")
    device: Mapped["Device"] = relationship("Device", back_populates="recommendations")
