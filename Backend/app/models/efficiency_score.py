import datetime
from typing import Any, Dict, Optional
from sqlalchemy import ForeignKey, DateTime, Float, String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class EfficiencyScore(Base):
    __tablename__ = "efficiency_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    period_type: Mapped[str] = mapped_column(String(20), nullable=False)  # weekly | monthly
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    # JSON structure: {"safety": 85, "gas_efficiency": 70, "cooking_efficiency": 60, "rec_compliance": 80, "cylinder_util": 90}
    component_scores_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    computed_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )

    # Relationships
    device: Mapped["Device"] = relationship("Device", back_populates="efficiency_scores")
