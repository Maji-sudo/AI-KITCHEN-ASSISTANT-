from datetime import datetime, timezone, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.device import Device
from app.models.gas_reading import GasReading
from app.models.leak_event import LeakEvent
from app.repositories.device_repository import device_repo
from app.repositories.telemetry_repository import gas_reading_repo, leak_event_repo
from app.schemas.safety import SafetyStatusResponse, ActiveLeakResponse, LeakHistoryResponse


class SafetyReadService:
    MAX_LIMIT = 1000

    def _get_device(self, db: Session, device_id: str, user_id: int) -> Device:
        device = device_repo.get(db, id=device_id)
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
        if device.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this device")
        return device

    def get_current_safety(self, db: Session, device_id: str, user_id: int) -> SafetyStatusResponse:
        device = self._get_device(db, device_id, user_id)
        latest = gas_reading_repo.get_latest_for_device(db, device_id=device_id, limit=1)
        latest_reading: Optional[GasReading] = latest[0] if latest else None
        connection_status = "unknown"
        last_seen: Optional[datetime] = None
        if latest_reading:
            last_seen = latest_reading.timestamp
            now = datetime.now(timezone.utc)
            compare_time = last_seen
            if compare_time.tzinfo is None:
                compare_time = compare_time.replace(tzinfo=timezone.utc)
            if now - compare_time <= timedelta(minutes=5):
                connection_status = "online"
            else:
                connection_status = "offline"
        return SafetyStatusResponse(
            device_id=device.id,
            latest_gas_ppm=latest_reading.ppm_value if latest_reading else None,
            timestamp=latest_reading.timestamp if latest_reading else None,
            status=latest_reading.status if latest_reading else None,
            valve_status=device.valve_status,
            connection_status=connection_status,
            last_seen=last_seen,
            source=latest_reading.source if latest_reading and latest_reading.source else "IOT",
        )

    def get_gas_history(
        self,
        db: Session,
        device_id: str,
        user_id: int,
        limit: int = 100,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[GasReading]:
        self._get_device(db, device_id, user_id)
        limit = min(limit, self.MAX_LIMIT)
        query = db.query(GasReading).filter(GasReading.device_id == device_id)
        if start:
            query = query.filter(GasReading.timestamp >= start)
        if end:
            query = query.filter(GasReading.timestamp <= end)
        readings = query.order_by(GasReading.timestamp.desc()).limit(limit).all()
        return list(reversed(readings))

    def get_active_leak(self, db: Session, device_id: str, user_id: int) -> Optional[ActiveLeakResponse]:
        self._get_device(db, device_id, user_id)
        unresolved = leak_event_repo.get_unresolved_for_device(db, device_id=device_id)
        if not unresolved:
            return None
        leak = unresolved[0]
        return ActiveLeakResponse(
            id=leak.id,
            device_id=leak.device_id,
            start_time=leak.start_time,
            end_time=leak.end_time,
            peak_ppm=leak.peak_ppm,
            auto_shutoff_triggered=leak.auto_shutoff_triggered,
            false_alarm=leak.false_alarm,
            notification_id=getattr(leak, "notification_id", None),
            active=True,
        )

    def get_leak_history(
        self,
        db: Session,
        device_id: str,
        user_id: int,
        limit: int = 100,
    ) -> LeakHistoryResponse:
        self._get_device(db, device_id, user_id)
        limit = min(limit, self.MAX_LIMIT)
        leaks = (
            db.query(LeakEvent)
            .filter(LeakEvent.device_id == device_id)
            .order_by(LeakEvent.start_time.desc())
            .limit(limit)
            .all()
        )
        items = []
        for leak in leaks:
            items.append(
                ActiveLeakResponse(
                    id=leak.id,
                    device_id=leak.device_id,
                    start_time=leak.start_time,
                    end_time=leak.end_time,
                    peak_ppm=leak.peak_ppm,
                    auto_shutoff_triggered=leak.auto_shutoff_triggered,
                    false_alarm=leak.false_alarm,
                    notification_id=getattr(leak, "notification_id", None),
                    active=leak.end_time is None,
                )
            )
        return LeakHistoryResponse(leaks=items)


safety_read_service = SafetyReadService()
