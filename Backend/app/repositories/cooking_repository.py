from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.base_repository import CRUDBase
from app.models.dish import Dish
from app.models.cooking_history import CookingHistory
from app.schemas.cooking import DishCreate, CookingHistoryCreate, CookingHistoryUpdate
from pydantic import BaseModel

class DishRepository(CRUDBase[Dish, DishCreate, BaseModel]):
    def get_by_name(self, db: Session, *, dish_name: str) -> Optional[Dish]:
        return db.query(Dish).filter(Dish.dish_name == dish_name).first()

class CookingHistoryRepository(CRUDBase[CookingHistory, CookingHistoryCreate, CookingHistoryUpdate]):
    def get_by_user(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> List[CookingHistory]:
        return db.query(CookingHistory).filter(CookingHistory.user_id == user_id).offset(skip).limit(limit).all()

    def get_by_device(self, db: Session, *, device_id: str, skip: int = 0, limit: int = 100) -> List[CookingHistory]:
        return db.query(CookingHistory).filter(CookingHistory.device_id == device_id).offset(skip).limit(limit).all()

dish_repo = DishRepository(Dish)
cooking_history_repo = CookingHistoryRepository(CookingHistory)
