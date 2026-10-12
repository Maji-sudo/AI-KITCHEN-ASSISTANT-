from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class BookingBase(BaseModel):
    distributor: str
    status: Optional[str] = "pending"
    source: Optional[str] = "app"

class BookingCreate(BookingBase):
    user_id:  Optional[int] = None
    device_id: str
    booking_date: datetime

class BookingUpdate(BaseModel):
    status: Optional[str] = None
    distributor: Optional[str] = None

class BookingResponse(BookingBase):
    id: int
    user_id: int
    device_id: str
    booking_date: datetime

    class Config:
        from_attributes = True
