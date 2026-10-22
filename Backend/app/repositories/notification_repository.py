import datetime
from typing import List, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.repositories.base_repository import CRUDBase
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate, NotificationUpdate


class NotificationRepository(CRUDBase[Notification, NotificationCreate, NotificationUpdate]):
    def get_by_user(
        self,
        db: Session,
        *,
        user_id: int,
        filter_type: Optional[str] = None,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Notification]:
        query = db.query(Notification).filter(Notification.user_id == user_id)

        if unread_only or filter_type == "unread":
            query = query.filter(Notification.read == False)
        elif filter_type == "safety":
            query = query.filter(Notification.channel.in_(["safety", "emergency"]))
        elif filter_type == "reminder":
            query = query.filter(Notification.channel.in_(["refill", "reminder"]))

        return (
            query.order_by(Notification.sent_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_unread(self, db: Session, *, user_id: int) -> int:
        return (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.read == False)
            .count()
        )

    def mark_as_read(self, db: Session, *, notification_id: int, user_id: int) -> Optional[Notification]:
        notif = (
            db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .first()
        )
        if not notif:
            return None
        notif.read = True
        db.commit()
        db.refresh(notif)
        return notif

    def mark_all_read(self, db: Session, *, user_id: int) -> int:
        updated = (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.read == False)
            .update({"read": True}, synchronize_session=False)
        )
        db.commit()
        return updated

    def delete_for_user(self, db: Session, *, notification_id: int, user_id: int) -> bool:
        notif = (
            db.query(Notification)
            .filter(Notification.id == notification_id, Notification.user_id == user_id)
            .first()
        )
        if not notif:
            return False
        db.delete(notif)
        db.commit()
        return True

    def clear_for_user(self, db: Session, *, user_id: int, only_read: bool = True) -> int:
        query = db.query(Notification).filter(Notification.user_id == user_id)
        if only_read:
            query = query.filter(Notification.read == True)
        deleted = query.delete(synchronize_session=False)
        db.commit()
        return deleted

    def find_recent_similar(
        self,
        db: Session,
        *,
        user_id: int,
        channel: str,
        notif_type: Optional[str] = None,
        device_id: Optional[str] = None,
        within_minutes: int = 30,
    ) -> Optional[Notification]:
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=within_minutes)
        query = (
            db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.channel == channel)
            .filter(Notification.sent_at >= cutoff)
        )
        candidates = query.all()
        for n in candidates:
            payload = n.payload or {}
            if notif_type and payload.get("type") != notif_type:
                continue
            if device_id and payload.get("device_id") != device_id:
                continue
            return n
        return None


notification_repo = NotificationRepository(Notification)
