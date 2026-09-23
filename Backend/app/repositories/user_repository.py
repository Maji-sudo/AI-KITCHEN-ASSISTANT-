from typing import Optional
from sqlalchemy.orm import Session
from app.repositories.base_repository import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserRepository(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def get_by_phone(self, db: Session, *, phone: str) -> Optional[User]:
        return db.query(User).filter(User.phone == phone).first()


user_repo = UserRepository(User)
