from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    name: str
    phone: Optional[str] = None
    email: EmailStr
    language_pref: Optional[str] = "en"


class UserCreate(UserBase):
    pass


# UserUpdate — all fields Optional so partial updates work
class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    language_pref: Optional[str] = None
    delivery_address: Optional[Dict[str, Any]] = None
    notification_preferences: Optional[Dict[str, Any]] = None
    safety_preferences: Optional[Dict[str, Any]] = None


class UserResponse(UserBase):
    id: int
    created_at: datetime
    delivery_address: Optional[Dict[str, Any]] = None
    notification_preferences: Optional[Dict[str, Any]] = None
    safety_preferences: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# Used by PATCH /auth/me — profile update (no password change here)
class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    language_pref: Optional[str] = None
    delivery_address: Optional[Dict[str, Any]] = None
    notification_preferences: Optional[Dict[str, Any]] = None
    safety_preferences: Optional[Dict[str, Any]] = None
