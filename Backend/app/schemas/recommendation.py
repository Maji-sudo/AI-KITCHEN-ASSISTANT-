from typing import Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field


# --- Base ---
class RecommendationBase(BaseModel):
    category: str                                     # safety | efficiency | cooking | refill | general
    message: str
    supporting_facts_json: Optional[Dict[str, Any]] = None
    confidence: float
    priority: int = 3                                 # 1=critical | 2=high | 3=medium | 4=low
    status: Optional[str] = "active"


# --- Create (internal engine use) ---
class RecommendationCreate(RecommendationBase):
    user_id: int
    device_id: str


# --- Update (dismiss / act) ---
class RecommendationUpdate(BaseModel):
    status: str


# --- Response ---
class RecommendationResponse(RecommendationBase):
    id: int
    user_id: int
    device_id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Generate endpoint request / response ---
class GenerateRequest(BaseModel):
    device_id: str
    days: int = Field(default=30, ge=7, le=180, description="Look-back window in days for analytics signals")


class GenerateResponse(BaseModel):
    device_id: str
    generated: int                  # number of new recommendations persisted
    rules_triggered: list[str]      # rule IDs that fired, e.g. ["R01", "R03"]
    message: str
