import logging
from typing import List, Optional
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.repositories.telemetry_repository import (
    gas_reading_repo,
    weight_reading_repo,
    leak_event_repo,
)
from app.schemas.telemetry import (
    GasReadingCreate,
    WeightReadingCreate,
    LeakEventCreate,
    LeakEventUpdate,
)
from app.models.gas_reading import GasReading
from app.models.weight_reading import WeightReading
from app.models.leak_event import LeakEvent
from app.models.device import Device
from app.services.notification_service import notification_service
from app.services.valve_command_service import valve_command_service
from app.services.system_log_service import system_log_service

logger = logging.getLogger(__name__)

# ── Gas-level thresholds (LPG standard, in PPM) ──────────────────────────
PPM_WARNING_THRESHOLD = 500     # elevated — could be stove residual
PPM_CRITICAL_THRESHOLD = 1000   # dangerous — likely leak


class TelemetryService:

    # ==================================================================
    # HELPER — resolve device → user
    # ==================================================================
    def _get_device_owner_id(self, db: Session, device_id: str) -> Optional[int]:
        """Look up the user_id that owns a device. Returns None if orphaned."""
        device = db.query(Device).filter(Device.id == device_id).first()
        if device and device.user_id:
            return device.user_id
        return None

    # ==================================================================
    # GAS READINGS  (with automatic leak detection)
    # ==================================================================
    def record_gas_reading(
        self, db: Session, reading_in: GasReadingCreate
    ) -> GasReading:
        """
        Ingest a gas sensor reading and run threshold-based safety checks.

        Thresholds (LPG industry standard):
          < 500 PPM  → normal
          500–999     → warning  (notify user)
          ≥ 1000      → critical (auto-create LeakEvent + emergency alert)
        """
        ppm = reading_in.ppm_value

        # ── Classify using shared service ────────────────────────
        from app.services.safety_classification import classify_gas
        reading_in.status = classify_gas(ppm)

        # ── Persist reading ───────────────────────────────────────────
        saved_reading = gas_reading_repo.create(db, obj_in=reading_in)

        # ── React to elevated levels ──────────────────────────────────
        if reading_in.status == "critical":
            logger.critical(
                "CRITICAL gas reading — device=%s  ppm=%.1f",
                reading_in.device_id, ppm,
            )
            self._handle_critical_gas(db, reading_in.device_id, ppm)

        elif reading_in.status == "warning":
            logger.warning(
                "WARNING gas reading — device=%s  ppm=%.1f",
                reading_in.device_id, ppm,
            )
            self._handle_warning_gas(db, reading_in.device_id, ppm)
            
        else:
            self._handle_normal_gas(db, reading_in.device_id)

        # ── Publish real-time safety update ───────────────────────────
        try:
            from app.services.safety_read_service import safety_read_service
            from app.services.realtime_service import realtime_manager
            
            user_id = self._get_device_owner_id(db, reading_in.device_id)
            if user_id:
                safety_status = safety_read_service.get_current_safety(db, reading_in.device_id, user_id)
                
                payload = {
                    "type": "SAFETY_UPDATE",
                    "data": safety_status.model_dump(mode='json')
                }
                realtime_manager.publish_safety_update(reading_in.device_id, payload)
        except Exception as e:
            logger.error("Failed to publish real-time safety update for device %s: %s", reading_in.device_id, e)

        return saved_reading

    def _handle_critical_gas(
        self, db: Session, device_id: str, ppm: float
    ) -> None:
        """Enforce Leak Event state machine for critical gas readings."""
        
        # 1) Query for an existing active LeakEvent
        active_leaks = self.get_unresolved_leaks(db, device_id)
        if active_leaks:
            # Maintain active leak, update peak_ppm if necessary
            leak = active_leaks[0]
            if ppm > leak.peak_ppm:
                leak_event_repo.update(
                    db,
                    db_obj=leak,
                    obj_in=LeakEventUpdate(peak_ppm=ppm)
                )
            return

        # 2) Create a new LeakEvent if none exists
        leak_in = LeakEventCreate(
            device_id=device_id,
            start_time=datetime.now(timezone.utc),
            peak_ppm=ppm,
            auto_shutoff_triggered=True,
            false_alarm=False,
        )
        self.record_leak_event(db, event_in=leak_in)
        
        # 3) Issue emergency close command
        device = db.query(Device).filter(Device.id == device_id).first()
        if device:
            valve_command_service.issue_emergency_close(db, device)

        # 4) Write system log
        system_log_service.log(
            db,
            device_id=device_id,
            log_level="CRITICAL",
            message=f"Auto-created leak event & shut off valve — PPM {ppm:.0f} exceeded critical threshold {PPM_CRITICAL_THRESHOLD}",
        )

    # ── Warning gas handler ───────────────────────────────────────────
    def _handle_warning_gas(
        self, db: Session, device_id: str, ppm: float
    ) -> None:
        """Send a warning notification to the device owner."""
        user_id = self._get_device_owner_id(db, device_id)
        if user_id:
            notification_service.send_safety_warning(
                db,
                user_id=user_id,
                device_id=device_id,
                ppm_value=ppm,
            )
        system_log_service.log(
            db,
            device_id=device_id,
            log_level="WARNING",
            message=f"Gas warning — PPM {ppm:.0f} exceeded warning threshold {PPM_WARNING_THRESHOLD}",
        )
        
    def _handle_normal_gas(self, db: Session, device_id: str) -> None:
        """Auto-resolve active leaks when gas drops to normal."""
        active_leaks = self.get_unresolved_leaks(db, device_id)
        for leak in active_leaks:
            self.resolve_leak_event(db, event_id=leak.id)
            system_log_service.log(
                db,
                device_id=device_id,
                log_level="INFO",
                message=f"Auto-resolved leak event {leak.id} as gas dropped to normal",
            )

    def get_recent_gas_readings(
        self, db: Session, device_id: str, limit: int = 100
    ) -> List[GasReading]:
        return gas_reading_repo.get_latest_for_device(
            db, device_id=device_id, limit=limit
        )

    # ==================================================================
    # WEIGHT READINGS
    # ==================================================================
    def record_weight_reading(
        self, db: Session, reading_in: WeightReadingCreate
    ) -> WeightReading:
        return weight_reading_repo.create(db, obj_in=reading_in)

    def get_recent_weight_readings(
        self, db: Session, device_id: str, limit: int = 100
    ) -> List[WeightReading]:
        return weight_reading_repo.get_latest_for_device(
            db, device_id=device_id, limit=limit
        )

    # ==================================================================
    # LEAK EVENTS
    # ==================================================================
    def record_leak_event(
        self, db: Session, event_in: LeakEventCreate
    ) -> LeakEvent:
        """Save a leak event AND fire an emergency notification to the device owner."""
        leak = leak_event_repo.create(db, obj_in=event_in)

        # ── Notify device owner ───────────────────────────────────────
        user_id = self._get_device_owner_id(db, event_in.device_id)
        if user_id:
            notif = notification_service.send_emergency_alert(
                db,
                user_id=user_id,
                device_id=event_in.device_id,
                ppm_value=event_in.peak_ppm,
            )
            # link notification to leak event
            leak_event_repo.update(
                db,
                db_obj=leak,
                obj_in=LeakEventUpdate(notification_id=notif.id),
            )
        else:
            logger.warning(
                "Leak event recorded for device %s but no owner found — cannot notify.",
                event_in.device_id,
            )

        return leak

    def resolve_leak_event(
        self, db: Session, event_id: int
    ) -> Optional[LeakEvent]:
        event = leak_event_repo.get(db, id=event_id)
        if event:
            return leak_event_repo.update(
                db,
                db_obj=event,
                obj_in=LeakEventUpdate(end_time=datetime.now(timezone.utc)),
            )
        return None

    def get_unresolved_leaks(
        self, db: Session, device_id: str
    ) -> List[LeakEvent]:
        return leak_event_repo.get_unresolved_for_device(
            db, device_id=device_id
        )


telemetry_service = TelemetryService()
