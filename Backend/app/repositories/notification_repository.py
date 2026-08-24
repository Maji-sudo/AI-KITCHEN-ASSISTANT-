from typing import List
from sqlalchemy.orm import Session
from app.repositories.base_repository import CRUDBase
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate, NotificationUpdate
from pydantic import BaseModel

class NotificationRepository(CRUDBase[Notification, NotificationCreate, NotificationUpdate]):
    def get_by_user(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 50) -> List[Notification]:
        return (
            db.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.sent_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

notification_repo = NotificationRepository(Notification)
