import logging
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.repositories.notification_repository import notification_repo
from app.schemas.notification import NotificationCreate, NotificationUpdate
from app.models.notification import Notification

logger = logging.getLogger(__name__)


class NotificationService:

    def send_notification(self, db: Session, user_id: int, channel: str, payload: dict) -> Notification:
        notification_in = NotificationCreate(
            user_id=user_id,
            channel=channel,
            payload=payload,
            delivery_status="pending",
            sent_at=datetime.now(timezone.utc),
        )
        # TODO: Integrate real FCM / SMS / WhatsApp delivery here
        notif = notification_repo.create(db, obj_in=notification_in)
        # Mark as sent after dispatching
        notification_repo.update(db, db_obj=notif, obj_in=NotificationUpdate(delivery_status="sent"))
        return notif

    # ── Emergency gas leak alert ──────────────────────────────────────────
    def send_emergency_alert(
        self,
        db: Session,
        user_id: int,
        device_id: str,
        ppm_value: float,
    ) -> Notification:
        """Fire a CRITICAL gas-leak notification to the device owner."""
        payload = {
            "type": "GAS_LEAK_CRITICAL",
            "severity": "critical",
            "device_id": device_id,
            "ppm_value": ppm_value,
            "message": (
                f"🚨 CRITICAL GAS LEAK DETECTED! PPM level: {ppm_value:.0f}. "
                f"Device {device_id} — shut off gas immediately and ventilate."
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        logger.critical(
            "GAS LEAK ALERT — device=%s  ppm=%.1f  user=%s",
            device_id, ppm_value, user_id,
        )
        return self.send_notification(db, user_id=user_id, channel="emergency", payload=payload)

    # ── Warning-level gas alert ───────────────────────────────────────────
    def send_safety_warning(
        self,
        db: Session,
        user_id: int,
        device_id: str,
        ppm_value: float,
    ) -> Notification:
        """Fire a WARNING gas-level notification to the device owner."""
        payload = {
            "type": "GAS_LEVEL_WARNING",
            "severity": "warning",
            "device_id": device_id,
            "ppm_value": ppm_value,
            "message": (
                f"⚠️ Elevated gas level detected. PPM: {ppm_value:.0f}. "
                f"Device {device_id} — check for leaks and ensure ventilation."
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        logger.warning(
            "GAS WARNING — device=%s  ppm=%.1f  user=%s",
            device_id, ppm_value, user_id,
        )
        return self.send_notification(db, user_id=user_id, channel="safety", payload=payload)

    def get_user_notifications(self, db: Session, user_id: int, skip: int = 0, limit: int = 50) -> List[Notification]:
        return notification_repo.get_by_user(db, user_id=user_id, skip=skip, limit=limit)


notification_service = NotificationService()
