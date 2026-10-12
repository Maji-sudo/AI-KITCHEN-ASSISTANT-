import pytest
from datetime import datetime, timezone, timedelta
from app.models.device import Device
from app.models.gas_reading import GasReading
from tests.conftest import client, TestingSessionLocal

def setup_device_state(db, device_id="paired_dev_1", battery=None, signal=None, health="healthy", valve="OPEN", paired=True, user_id=1, calibrated=None):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        device = Device(id=device_id, name="Test Device")
        db.add(device)
    device.user_id = user_id if paired else None
    device.battery_level = battery
    device.signal_strength = signal
    device.sensor_health_status = health
    device.valve_status = valve
    device.last_calibrated_at = calibrated
    db.commit()
    db.refresh(device)
    return device

def setup_telemetry(db, device_id="paired_dev_1", offset_minutes=0, ppm=500):
    timestamp = datetime.now(timezone.utc) - timedelta(minutes=offset_minutes)
    reading = GasReading(device_id=device_id, ppm_value=ppm, status="warning", timestamp=timestamp)
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading

def clear_data(db, device_id="paired_dev_1"):
    db.query(GasReading).filter(GasReading.device_id == device_id).delete()
    db.commit()

def test_owner_can_retrieve_diagnostics():
    """TEST 1: Authenticated owner can retrieve diagnostics for their device."""
    db = TestingSessionLocal()
    setup_device_state(db)
    db.close()
    
    response = client.get("/api/v1/devices/paired_dev_1/diagnostics")
    assert response.status_code == 200
    data = response.json()
    assert data["device"]["id"] == "paired_dev_1"

def test_unauthorized_user_cannot_retrieve_diagnostics():
    """TEST 2: Unauthorized user cannot retrieve another user's diagnostics. Expected: HTTP 403."""
    db = TestingSessionLocal()
    setup_device_state(db, device_id="other_dev", user_id=999)
    db.close()
    
    response = client.get("/api/v1/devices/other_dev/diagnostics")
    assert response.status_code == 403

def test_latest_gas_reading_returned():
    """TEST 3: Latest persisted gas reading is returned correctly."""
    db = TestingSessionLocal()
    clear_data(db)
    setup_device_state(db)
    setup_telemetry(db, ppm=700) # Latest
    db.close()

    response = client.get("/api/v1/devices/paired_dev_1/diagnostics")
    data = response.json()
    assert data["telemetry"]["latest_gas_ppm"] == 700.0

def test_battery_and_signal_returned():
    """TEST 4: Battery level is returned when available. TEST 5: Signal strength is returned when available."""
    db = TestingSessionLocal()
    setup_device_state(db, battery=85, signal=-60)
    db.close()

    response = client.get("/api/v1/devices/paired_dev_1/diagnostics")
    data = response.json()
    assert data["sensor"]["battery_level"] == 85
    assert data["sensor"]["signal_strength"] == -60

def test_missing_battery_signal_null():
    """TEST 6: Missing battery/signal values are returned as null/unknown, not fake values."""
    db = TestingSessionLocal()
    setup_device_state(db, battery=None, signal=None)
    db.close()

    response = client.get("/api/v1/devices/paired_dev_1/diagnostics")
    data = response.json()
    assert data["sensor"]["battery_level"] is None
    assert data["sensor"]["signal_strength"] is None

def test_sensor_health_returned():
    """TEST 7: Sensor health is returned from the persisted device state."""
    db = TestingSessionLocal()
    setup_device_state(db, health="warning")
    db.close()

    response = client.get("/api/v1/devices/paired_dev_1/diagnostics")
    data = response.json()
    assert data["sensor"]["health"] == "warning"

def test_missing_health_is_unknown():
    """TEST 8: Missing/unknown health is not falsely reported as healthy."""
    db = TestingSessionLocal()
    # Explicitly set to None to bypass default "healthy" logic if possible, or "unknown"
    setup_device_state(db, health="unknown")
    db.close()

    response = client.get("/api/v1/devices/paired_dev_1/diagnostics")
    data = response.json()
    assert data["sensor"]["health"] == "unknown"

def test_calibration_returned():
    """TEST 9: Last calibration timestamp is returned when available."""
    db = TestingSessionLocal()
    now = datetime.now(timezone.utc)
    setup_device_state(db, calibrated=now)
    db.close()

    response = client.get("/api/v1/devices/paired_dev_1/diagnostics")
    data = response.json()
    assert data["sensor"]["last_calibrated_at"] is not None

def test_connection_status_online():
    """TEST 10: Connection status is derived from actual available telemetry/heartbeat information."""
    db = TestingSessionLocal()
    clear_data(db)
    setup_device_state(db)
    setup_telemetry(db, offset_minutes=1) # 1 minute ago -> online
    db.close()

    response = client.get("/api/v1/devices/paired_dev_1/diagnostics")
    data = response.json()
    assert data["connection"]["status"] == "online"

def test_connection_status_offline():
    """Test offline connection status derivation."""
    db = TestingSessionLocal()
    clear_data(db)
    setup_device_state(db)
    setup_telemetry(db, offset_minutes=10) # 10 minutes ago -> offline
    db.close()

    response = client.get("/api/v1/devices/paired_dev_1/diagnostics")
    data = response.json()
    assert data["connection"]["status"] == "offline"

def test_no_telemetry_reports_unknown():
    """TEST 11: No telemetry/heartbeat information does not falsely report ONLINE."""
    db = TestingSessionLocal()
    clear_data(db)
    setup_device_state(db)
    db.close()

    response = client.get("/api/v1/devices/paired_dev_1/diagnostics")
    data = response.json()
    assert data["connection"]["status"] == "unknown"

def test_software_valve_status_returned():
    """TEST 12: Software valve status is returned correctly."""
    db = TestingSessionLocal()
    setup_device_state(db, valve="CLOSED")
    db.close()

    response = client.get("/api/v1/devices/paired_dev_1/diagnostics")
    data = response.json()
    assert data["safety"]["valve_status"] == "CLOSED"

def test_no_physical_actuation_claim():
    """TEST 13: Diagnostics do not claim physical valve actuation.
    (Validated by schema not containing 'physical_actuation' or similar)."""
    response = client.get("/api/v1/devices/paired_dev_1/diagnostics")
    data = response.json()
    assert "valve_status" in data["safety"]
    assert "hardware_confirmed" not in data["safety"]
    assert "physical_state" not in data["safety"]

def test_nonexistent_device():
    """TEST 14: Nonexistent device is handled correctly."""
    response = client.get("/api/v1/devices/nonexistent/diagnostics")
    assert response.status_code == 404
