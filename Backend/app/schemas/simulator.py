from typing import Optional
from pydantic import BaseModel, Field


class SimulatorStartRequest(BaseModel):
    device_id: str
    baseline_ppm: float = 300.0
    interval_seconds: float = Field(default=1.0, gt=0)
    count: Optional[int] = Field(default=None, ge=1)
    mode: Optional[str] = "fluctuate"  # "fluctuate", "spike", "increase", "decrease"


class SimulatorStopRequest(BaseModel):
    device_id: str


class SimulatorStatusResponse(BaseModel):
    device_id: str
    running: bool
    generated_count: int
    baseline_ppm: Optional[float] = None
    last_ppm: Optional[float] = None
    interval_seconds: Optional[float] = None
    mode: Optional[str] = None
