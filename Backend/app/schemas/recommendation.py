from typing import Optional, Any, Dict
from pydantic import BaseModel

# --- Recommendation ---
class RecommendationBase(BaseModel):
    category: str
    message: str
    supporting_facts_json: Optional[Dict[str, Any]] = None
    confidence: float
    status: Optional[str] = "active"

class RecommendationCreate(RecommendationBase):
    user_id: int
    device_id: str

class RecommendationUpdate(BaseModel):
    status: str

class RecommendationResponse(RecommendationBase):
    id: int
    user_id: int
    device_id: str

    class Config:
        from_attributes = True
