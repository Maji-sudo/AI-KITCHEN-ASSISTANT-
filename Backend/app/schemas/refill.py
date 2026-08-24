from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class RefillPredictionBase(BaseModel):
    predicted_empty_date: datetime
    days_left: int
    confidence: float

class RefillPredictionCreate(RefillPredictionBase):
    device_id: str

class RefillPredictionResponse(RefillPredictionBase):
    id: int
    device_id: str
    computed_at: datetime

    class Config:
        from_attributes = True
