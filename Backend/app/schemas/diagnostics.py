from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class DiagnosticDeviceNode(BaseModel):
    id: str
    name: str
    paired: bool

class DiagnosticConnectionNode(BaseModel):
    status: str  # online, offline, unknown
    last_seen: Optional[datetime] = None

class DiagnosticSensorNode(BaseModel):
    health: str
    battery_level: Optional[int] = None
    signal_strength: Optional[int] = None
    last_calibrated_at: Optional[datetime] = None

class DiagnosticTelemetryNode(BaseModel):
    latest_gas_ppm: Optional[float] = None
    timestamp: Optional[datetime] = None
    source: Optional[str] = None

class DiagnosticSafetyNode(BaseModel):
    valve_status: str

class DeviceDiagnosticsResponse(BaseModel):
    device: DiagnosticDeviceNode
    connection: DiagnosticConnectionNode
    sensor: DiagnosticSensorNode
    telemetry: DiagnosticTelemetryNode
    safety: DiagnosticSafetyNode
