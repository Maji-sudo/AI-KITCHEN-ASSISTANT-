from typing import Optional
from datetime import datetime
from pydantic import BaseModel

# --- Gas Reading ---
class GasReadingBase(BaseModel):
    ppm_value: float
    status: str = "normal"  # normal | warning | critical
    timestamp: datetime

class GasReadingCreate(GasReadingBase):
    device_id: str

class GasReadingResponse(GasReadingBase):
    id: int
    device_id: str

    class Config:
        from_attributes = True

# --- Weight Reading ---
class WeightReadingBase(BaseModel):
    weight_g: float
    timestamp: datetime

class WeightReadingCreate(WeightReadingBase):
    device_id: str

class WeightReadingResponse(WeightReadingBase):
    id: int
    device_id: str

    class Config:
        from_attributes = True

# --- Leak Event ---
class LeakEventBase(BaseModel):
    start_time: datetime
    end_time: Optional[datetime] = None
    peak_ppm: float
    auto_shutoff_triggered: Optional[bool] = False
    false_alarm: Optional[bool] = False

class LeakEventCreate(LeakEventBase):
    device_id: str

class LeakEventUpdate(BaseModel):
    end_time: Optional[datetime] = None
    peak_ppm: Optional[float] = None
    auto_shutoff_triggered: Optional[bool] = None
    false_alarm: Optional[bool] = None

class LeakEventResponse(LeakEventBase):
    id: int
    device_id: str

    class Config:
        from_attributes = True
