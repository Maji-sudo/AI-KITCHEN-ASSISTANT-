from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    name: str
    phone: str
    email: Optional[EmailStr] = None
    language_pref: Optional[str] = "en"


class UserCreate(UserBase):
    pass


# UserUpdate does NOT inherit UserBase so all fields can be Optional
class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    language_pref: Optional[str] = None


class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
