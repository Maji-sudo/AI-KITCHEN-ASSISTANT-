from typing import Optional
from datetime import datetime
from pydantic import BaseModel

# --- Gas Reading ---
class GasReadingBase(BaseModel):
    ppm_value: Optional[float] = 0.0
    mq2_raw: Optional[float] = None
    mq2_ppm: Optional[float] = None
    mq5_raw: Optional[float] = None
    mq5_ppm: Optional[float] = None
    mq9_raw: Optional[float] = None
    mq9_ppm: Optional[float] = None
    status: str = "normal"  # normal | warning | critical
    timestamp: datetime

    def __init__(self, **data):
        if "ppm_value" not in data or data.get("ppm_value") is None or data.get("ppm_value") == 0:
            ppms = [data.get("mq2_ppm"), data.get("mq5_ppm"), data.get("mq9_ppm")]
            valid_ppms = [p for p in ppms if p is not None]
            if valid_ppms:
                data["ppm_value"] = max(valid_ppms)
        super().__init__(**data)

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



