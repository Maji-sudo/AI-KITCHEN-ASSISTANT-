from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

# --- Dish ---
class DishBase(BaseModel):
    dish_name: str
    cuisine_tag: str
    base_gas_g: float
    base_duration_min: int

class DishCreate(DishBase):
    pass

class DishResponse(DishBase):
    id: int

    class Config:
        from_attributes = True

# --- Cooking History ---
class CookingHistoryBase(BaseModel):
    logged_date: datetime
    actual_gas_g: Optional[float] = None
    actual_duration_min: Optional[int] = None

class CookingHistoryCreate(CookingHistoryBase):
    user_id: int
    device_id: str
    dish_id: Optional[int] = None

class CookingHistoryUpdate(BaseModel):
    actual_gas_g: Optional[float] = None
    actual_duration_min: Optional[int] = None

class CookingHistoryResponse(CookingHistoryBase):
    id: int
    user_id: int
    device_id: str
    dish_id: Optional[int] = None
    dish: Optional[DishResponse] = None

    class Config:
        from_attributes = True

# --- Chat ---
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
