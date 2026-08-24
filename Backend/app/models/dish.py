from typing import List
from sqlalchemy import String, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class Dish(Base):
    __tablename__ = "dish_library"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dish_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    cuisine_tag: Mapped[str] = mapped_column(String(100), nullable=False)
    base_gas_g: Mapped[float] = mapped_column(Float, nullable=False)
    base_duration_min: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    cooking_history: Mapped[List["CookingHistory"]] = relationship("CookingHistory", back_populates="dish")
