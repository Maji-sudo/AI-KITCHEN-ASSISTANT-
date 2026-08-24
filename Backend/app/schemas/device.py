from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from pydantic import BaseModel, Field

# --- Cylinder Schemas ---
class CylinderBase(BaseModel):
    tare_weight_g: float
    full_weight_g: float
    cylinder_type: Optional[str] = "14.2kg"

class CylinderCreate(CylinderBase):
    device_id: str

class CylinderUpdate(BaseModel):
    tare_weight_g: Optional[float] = None
    full_weight_g: Optional[float] = None
    cylinder_type: Optional[str] = None

class CylinderResponse(CylinderBase):
    id: int
    device_id: str
    install_date: datetime

    class Config:
        from_attributes = True

# --- Device Schemas ---
class DeviceBase(BaseModel):
    name: str
    firmware_version: Optional[str] = None
    status: Optional[str] = "inactive"

class DeviceCreate(DeviceBase):
    id: str  # Usually MAC address or specific serial
    user_id: Optional[int] = None

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    firmware_version: Optional[str] = None
    status: Optional[str] = None
    user_id: Optional[int] = None

class DeviceResponse(DeviceBase):
    id: str
    user_id: Optional[int] = None
    paired_at: Optional[datetime] = None
    cylinders: List[CylinderResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True
