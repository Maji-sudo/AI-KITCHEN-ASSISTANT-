from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class DeviceCommandBase(BaseModel):
    command: str
    status: str = "RECORDED"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    executed_at: Optional[datetime] = None


class DeviceCommandCreate(DeviceCommandBase):
    device_id: str


class DeviceCommandUpdate(BaseModel):
    status: Optional[str] = None
    executed_at: Optional[datetime] = None


class DeviceCommandResponse(DeviceCommandBase):
    id: int
    device_id: str

    class Config:
        from_attributes = True
