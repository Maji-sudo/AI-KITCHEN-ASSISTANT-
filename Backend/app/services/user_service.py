from typing import Optional
from sqlalchemy.orm import Session
from app.repositories.user_repository import user_repo
from app.schemas.user import UserCreate, UserUpdate
from app.models.user import User

class UserService:
    def get_user(self, db: Session, user_id: int) -> Optional[User]:
        return user_repo.get(db, id=user_id)

    def get_user_by_phone(self, db: Session, phone: str) -> Optional[User]:
        return user_repo.get_by_phone(db, phone=phone)

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        return user_repo.get_by_email(db, email=email)

    def create_user(self, db: Session, user_in: UserCreate) -> User:
        return user_repo.create(db, obj_in=user_in)

    def update_user(self, db: Session, db_user: User, user_in: UserUpdate) -> User:
        return user_repo.update(db, db_obj=db_user, obj_in=user_in)

user_service = UserService()
