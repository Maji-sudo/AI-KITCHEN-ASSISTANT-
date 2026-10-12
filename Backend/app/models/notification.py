import datetime
from typing import Any, Dict, Optional
from sqlalchemy import ForeignKey, DateTime, String, Integer, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)  # fcm | sms | whatsapp
    payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    sent_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    delivery_status: Mapped[str] = mapped_column(String(50), default="pending")  # pending | sent | delivered | failed
    read: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")
