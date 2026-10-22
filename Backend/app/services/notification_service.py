import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.repositories.notification_repository import notification_repo
from app.schemas.notification import NotificationCreate, NotificationUpdate
from app.models.notification import Notification
from app.models.device import Device
from app.models.leak_event import LeakEvent
from app.models.refill_prediction import RefillPrediction
from app.models.cylinder import Cylinder
from app.models.weight_reading import WeightReading

logger = logging.getLogger(__name__)


class NotificationService:

    def send_notification(self, db: Session, user_id: int, channel: str, payload: dict) -> Notification:
        # Standardize payload structure
        if "body" not in payload and "message" in payload:
            payload["body"] = payload["message"]
        if "description" not in payload:
            payload["description"] = payload.get("body", "")
        if "timestamp" not in payload:
            payload["timestamp"] = datetime.now(timezone.utc).isoformat()

        notification_in = NotificationCreate(
            user_id=user_id,
            channel=channel,
            payload=payload,
            delivery_status="sent",
            sent_at=datetime.now(timezone.utc),
        )
        notif = notification_repo.create(db, obj_in=notification_in)
        return notif

    # ── Emergency gas leak alert ──────────────────────────────────────────
    def send_emergency_alert(
        self,
        db: Session,
        user_id: int,
        device_id: str,
        ppm_value: float,
        force: bool = False,
    ) -> Notification:
        """Fire a CRITICAL gas-leak notification to the device owner with deduplication."""
        if not force:
            # Deduplication check: avoid duplicate alert if one was created recently (within 5 minutes)
            existing = notification_repo.find_recent_similar(
                db,
                user_id=user_id,
                channel="emergency",
                notif_type="GAS_LEAK_CRITICAL",
                device_id=device_id,
                within_minutes=5,
            )
            if existing:
                logger.info("Deduplicating critical gas leak alert for device=%s user=%s", device_id, user_id)
                return existing

        payload = {
            "type": "GAS_LEAK_CRITICAL",
            "category": "safety",
            "severity": "critical",
            "device_id": device_id,
            "ppm_value": ppm_value,
            "title": "🚨 CRITICAL GAS LEAK DETECTED",
            "body": (
                f"🚨 CRITICAL GAS LEAK DETECTED! PPM level: {ppm_value:.0f}. "
                f"Device {device_id} — shut off gas immediately and ventilate."
            ),
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
    ) -> Optional[Notification]:
        """Fire a WARNING gas-level notification to the device owner with deduplication."""
        # Deduplication check: do not flood with warnings if sent within last 15 minutes
        existing = notification_repo.find_recent_similar(
            db,
            user_id=user_id,
            channel="safety",
            notif_type="GAS_LEVEL_WARNING",
            device_id=device_id,
            within_minutes=15,
        )
        if existing:
            logger.debug("Deduplicating warning gas alert for device=%s user=%s", device_id, user_id)
            return existing

        payload = {
            "type": "GAS_LEVEL_WARNING",
            "category": "safety",
            "severity": "warning",
            "device_id": device_id,
            "ppm_value": ppm_value,
            "title": "⚠️ Elevated Gas Level Warning",
            "body": (
                f"⚠️ Elevated gas level detected. PPM: {ppm_value:.0f}. "
                f"Device {device_id} — check for leaks and ensure ventilation."
            ),
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

    # ── Cylinder Refill Reminder ───────────────────────────────────────────
    def send_refill_reminder(
        self,
        db: Session,
        user_id: int,
        device_id: str,
        days_left: int,
        cylinder_pct: Optional[int] = None,
    ) -> Optional[Notification]:
        """Send cylinder refill reminder if not already sent in the last 24 hours."""
        existing = notification_repo.find_recent_similar(
            db,
            user_id=user_id,
            channel="refill",
            notif_type="CYLINDER_REFILL_REMINDER",
            device_id=device_id,
            within_minutes=1440,  # 24 hours
        )
        if existing:
            return existing

        pct_text = f" ({cylinder_pct}% remaining)" if cylinder_pct is not None else ""
        payload = {
            "type": "CYLINDER_REFILL_REMINDER",
            "category": "refill",
            "severity": "reminder",
            "device_id": device_id,
            "days_left": days_left,
            "cylinder_pct": cylinder_pct,
            "title": "🔥 Cylinder Refill Reminder",
            "body": (
                f"Your LPG cylinder on device {device_id} has approximately {days_left} days of gas left{pct_text}. "
                "Schedule a cylinder refill booking to avoid running out."
            ),
            "message": (
                f"Your LPG cylinder on device {device_id} has approximately {days_left} days of gas left{pct_text}. "
                "Schedule a cylinder refill booking to avoid running out."
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return self.send_notification(db, user_id=user_id, channel="refill", payload=payload)

    # ── Device Offline Alert ───────────────────────────────────────────────
    def send_device_offline_alert(
        self,
        db: Session,
        user_id: int,
        device_id: str,
        device_name: Optional[str] = None,
    ) -> Optional[Notification]:
        """Send device offline notification if not already sent in the last 12 hours."""
        existing = notification_repo.find_recent_similar(
            db,
            user_id=user_id,
            channel="safety",
            notif_type="DEVICE_OFFLINE",
            device_id=device_id,
            within_minutes=720,  # 12 hours
        )
        if existing:
            return existing

        name_text = f" ({device_name})" if device_name else ""
        payload = {
            "type": "DEVICE_OFFLINE",
            "category": "safety",
            "severity": "warning",
            "device_id": device_id,
            "title": "📡 Smart Device Offline",
            "body": (
                f"Device {device_id}{name_text} has lost Wi-Fi connectivity. "
                "Safety monitoring is paused until the scale reconnects."
            ),
            "message": (
                f"Device {device_id}{name_text} has lost Wi-Fi connectivity. "
                "Safety monitoring is paused until the scale reconnects."
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return self.send_notification(db, user_id=user_id, channel="safety", payload=payload)

    # ── Relevant System Event ──────────────────────────────────────────────
    def send_system_event(
        self,
        db: Session,
        user_id: int,
        title: str,
        message: str,
        severity: str = "info",
        device_id: Optional[str] = None,
    ) -> Notification:
        payload = {
            "type": "SYSTEM_EVENT",
            "category": "system",
            "severity": severity,
            "device_id": device_id,
            "title": title,
            "body": message,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return self.send_notification(db, user_id=user_id, channel="system", payload=payload)

    # ── Real Data Synchronization ─────────────────────────────────────────
    def sync_real_events_to_notifications(self, db: Session, user_id: int) -> None:
        """
        Inspect actual user devices, leak events, and cylinder telemetry,
        and generate persisted notifications for any unnotified real events.
        """
        user_devices = db.query(Device).filter(Device.user_id == user_id).all()
        for device in user_devices:
            # 1. Active or recent leak events
            active_leaks = (
                db.query(LeakEvent)
                .filter(LeakEvent.device_id == device.id, LeakEvent.end_time == None)
                .all()
            )
            for leak in active_leaks:
                self.send_emergency_alert(
                    db,
                    user_id=user_id,
                    device_id=device.id,
                    ppm_value=leak.peak_ppm,
                )

            # 2. Check cylinder refill status
            prediction = (
                db.query(RefillPrediction)
                .filter(RefillPrediction.device_id == device.id)
                .order_by(RefillPrediction.computed_at.desc())
                .first()
            )
            if prediction and prediction.days_left <= 5:
                # Calculate percentage if cylinder and weight available
                cylinder = db.query(Cylinder).filter(Cylinder.device_id == device.id).first()
                latest_weight = (
                    db.query(WeightReading)
                    .filter(WeightReading.device_id == device.id)
                    .order_by(WeightReading.timestamp.desc())
                    .first()
                )
                pct = None
                if cylinder and latest_weight and cylinder.full_weight_g > cylinder.tare_weight_g:
                    net_cap = cylinder.full_weight_g - cylinder.tare_weight_g
                    net_rem = max(0, latest_weight.weight_g - cylinder.tare_weight_g)
                    pct = min(100, max(0, round((net_rem / net_cap) * 100)))

                self.send_refill_reminder(
                    db,
                    user_id=user_id,
                    device_id=device.id,
                    days_left=prediction.days_left,
                    cylinder_pct=pct,
                )

            # 3. Check device offline status
            if device.status in ("inactive", "offline"):
                self.send_device_offline_alert(
                    db,
                    user_id=user_id,
                    device_id=device.id,
                    device_name=device.name,
                )

    def get_user_notifications(
        self,
        db: Session,
        user_id: int,
        filter_type: Optional[str] = None,
        unread_only: bool = False,
        skip: int = 0,
        limit: int = 50,
        sync: bool = True,
    ) -> List[Notification]:
        if sync:
            try:
                self.sync_real_events_to_notifications(db, user_id=user_id)
            except Exception as e:
                logger.warning("Failed to sync real events to notifications for user %s: %s", user_id, e)

        return notification_repo.get_by_user(
            db,
            user_id=user_id,
            filter_type=filter_type,
            unread_only=unread_only,
            skip=skip,
            limit=limit,
        )

    def get_unread_count(self, db: Session, user_id: int) -> int:
        return notification_repo.count_unread(db, user_id=user_id)

    def mark_as_read(self, db: Session, notification_id: int, user_id: int) -> Optional[Notification]:
        return notification_repo.mark_as_read(db, notification_id=notification_id, user_id=user_id)

    def mark_all_read(self, db: Session, user_id: int) -> int:
        return notification_repo.mark_all_read(db, user_id=user_id)

    def delete_notification(self, db: Session, notification_id: int, user_id: int) -> bool:
        return notification_repo.delete_for_user(db, notification_id=notification_id, user_id=user_id)

    def clear_notifications(self, db: Session, user_id: int, only_read: bool = True) -> int:
        return notification_repo.clear_for_user(db, user_id=user_id, only_read=only_read)


notification_service = NotificationService()
