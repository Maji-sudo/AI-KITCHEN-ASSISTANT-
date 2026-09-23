from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class SimulateDeviceRequest(BaseModel):
    name: Optional[str] = "Kitchen SafeGas Hub"
    cylinder_type: Optional[str] = "14.2kg"
    device_id: Optional[str] = None


class SimulateDataRequest(BaseModel):
    device_id: str
    days: int = Field(default=7, ge=1, le=60)
    pattern: str = Field(
        default="medium",
        description="Usage pattern: low, medium, high, weekend-heavy, or irregular"
    )


class SimulateSafetyRequest(BaseModel):
    device_id: str
    scenario: str = Field(
        default="normal",
        description="Safety scenario: normal, warning, or critical"
    )


class ResetDataRequest(BaseModel):
    device_id: str


class ManualCookingRequest(BaseModel):
    device_id: Optional[str] = None
    dish_name: Optional[str] = None
    dish_id: Optional[int] = None
    cooking_duration_min: int = 20
    actual_gas_g: float = 45.0
    logged_date: Optional[datetime] = None


class SimulationResponse(BaseModel):
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None
