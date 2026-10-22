from typing import Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel

# --- Notification ---
class NotificationBase(BaseModel):
    channel: str
    payload: Optional[Dict[str, Any]] = None
    delivery_status: Optional[str] = "pending"
    read: Optional[bool] = False

class NotificationCreate(NotificationBase):
    user_id: int
    sent_at: Optional[datetime] = None

class NotificationUpdate(BaseModel):
    delivery_status: Optional[str] = None
    read: Optional[bool] = None

class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    sent_at: datetime

    class Config:
        from_attributes = True


class UnreadCountResponse(BaseModel):
    unread_count: int
