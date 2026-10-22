from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class SafetyStatusResponse(BaseModel):
    device_id: str
    latest_gas_ppm: Optional[float] = None
    timestamp: Optional[datetime] = None
    status: Optional[str] = None  # normal | warning | critical
    valve_status: Optional[str] = None
    connection_status: Optional[str] = None  # online | offline | unknown
    last_seen: Optional[datetime] = None
    source: Optional[str] = "IOT"

    class Config:
        from_attributes = True

# Reuse existing GasReadingResponse for history
from app.schemas.telemetry import GasReadingResponse

class ActiveLeakResponse(BaseModel):
    id: int
    device_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    peak_ppm: float
    auto_shutoff_triggered: Optional[bool] = False
    false_alarm: Optional[bool] = False
    notification_id: Optional[int] = None
    active: bool = True

    class Config:
        from_attributes = True

class LeakHistoryResponse(BaseModel):
    leaks: List[ActiveLeakResponse]

    class Config:
        from_attributes = True
