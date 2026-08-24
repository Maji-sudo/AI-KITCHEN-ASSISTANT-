from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class SystemLogBase(BaseModel):
    log_level: str
    message: str

class SystemLogCreate(SystemLogBase):
    device_id: str

class SystemLogResponse(SystemLogBase):
    id: int
    device_id: str
    created_at: datetime

    class Config:
        from_attributes = True
