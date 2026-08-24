import datetime
from typing import Optional
from sqlalchemy import ForeignKey, DateTime, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class CookingHistory(Base):
    __tablename__ = "cooking_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    dish_id: Mapped[Optional[int]] = mapped_column(ForeignKey("dish_library.id", ondelete="SET NULL"), nullable=True)
    logged_date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_gas_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_duration_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="cooking_history")
    device: Mapped["Device"] = relationship("Device", back_populates="cooking_history")
    dish: Mapped[Optional["Dish"]] = relationship("Dish", back_populates="cooking_history")
