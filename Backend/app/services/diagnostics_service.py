from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.device import Device
from app.repositories.device_repository import device_repo
from app.services.telemetry_service import telemetry_service
from app.schemas.diagnostics import (
    DeviceDiagnosticsResponse,
    DiagnosticDeviceNode,
    DiagnosticConnectionNode,
    DiagnosticSensorNode,
    DiagnosticTelemetryNode,
    DiagnosticSafetyNode,
)

class DiagnosticsService:
    def get_diagnostics(self, db: Session, device_id: str, user_id: int) -> DeviceDiagnosticsResponse:
        # 1. Fetch and Verify Ownership
        device = device_repo.get(db, id=device_id)
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
        if device.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this device")

        # 2. Fetch Latest Telemetry
        recent_readings = telemetry_service.get_recent_gas_readings(db, device_id, limit=1)
        latest_reading = recent_readings[0] if recent_readings else None

        # 3. Connection Logic
        connection_status = "unknown"
        last_seen = None
        if latest_reading:
            last_seen = latest_reading.timestamp
            now = datetime.now(timezone.utc)
            
            # Ensure last_seen is timezone-aware for comparison
            compare_time = last_seen
            if compare_time.tzinfo is None:
                compare_time = compare_time.replace(tzinfo=timezone.utc)
                
            if now - compare_time <= timedelta(minutes=5):
                connection_status = "online"
            else:
                connection_status = "offline"

        # 4. Sensor Health
        health_status = device.sensor_health_status or "unknown"

        # 5. Build Response
        return DeviceDiagnosticsResponse(
            device=DiagnosticDeviceNode(
                id=device.id,
                name=device.name,
                paired=device.user_id is not None
            ),
            connection=DiagnosticConnectionNode(
                status=connection_status,
                last_seen=last_seen
            ),
            sensor=DiagnosticSensorNode(
                health=health_status,
                battery_level=device.battery_level,
                signal_strength=device.signal_strength,
                last_calibrated_at=device.last_calibrated_at
            ),
            telemetry=DiagnosticTelemetryNode(
                latest_gas_ppm=latest_reading.ppm_value if latest_reading else None,
                timestamp=latest_reading.timestamp if latest_reading else None,
                source=getattr(latest_reading, 'source', None) if latest_reading else None # source might not exist on model directly depending on Phase 1
            ),
            safety=DiagnosticSafetyNode(
                valve_status=device.valve_status or "unknown"
            )
        )

diagnostics_service = DiagnosticsService()
