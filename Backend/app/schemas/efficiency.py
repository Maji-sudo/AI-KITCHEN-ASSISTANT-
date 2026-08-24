from typing import Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel


# --- Efficiency Score ---
class EfficiencyScoreBase(BaseModel):
    period_type: str  # weekly | monthly
    overall_score: float
    component_scores_json: Optional[Dict[str, Any]] = None

class EfficiencyScoreCreate(EfficiencyScoreBase):
    device_id: str

class EfficiencyScoreResponse(EfficiencyScoreBase):
    id: int
    device_id: str
    computed_at: datetime

    class Config:
        from_attributes = True
