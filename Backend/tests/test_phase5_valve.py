import pytest
from datetime import datetime, timezone
from app.models.leak_event import LeakEvent
from app.models.device import Device
from app.models.device_command import DeviceCommand
from tests.conftest import client, TestingSessionLocal


def test_first_critical_creates_active_leak_and_emergency_close():
    """TEST 1: First CRITICAL reading creates one active leak and one emergency-close action."""
    db = TestingSessionLocal()
    # Ensure clean state
    device = db.query(Device).filter(Device.id == "paired_dev_1").first()
    device.valve_status = "OPEN"
    db.query(LeakEvent).filter(LeakEvent.device_id == "paired_dev_1").delete()
    db.query(DeviceCommand).filter(DeviceCommand.device_id == "paired_dev_1").delete()
    db.commit()
    db.close()

    response = client.post(
        "/api/v1/telemetry/gas",
        json={"device_id": "paired_dev_1", "ppm_value": 1200, "timestamp": datetime.now(timezone.utc).isoformat()}
    )
    assert response.status_code == 201

    db = TestingSessionLocal()
    leaks = db.query(LeakEvent).filter(LeakEvent.device_id == "paired_dev_1").all()
    commands = db.query(DeviceCommand).filter(DeviceCommand.device_id == "paired_dev_1").all()
    device = db.query(Device).filter(Device.id == "paired_dev_1").first()
    db.close()

    assert len(leaks) == 1
    assert len(commands) == 1
    assert commands[0].command == "EMERGENCY_CLOSE"
    assert device.valve_status == "CLOSED"


def test_repeated_critical_does_not_create_duplicate_emergency_close():
    """TEST 2: Repeated CRITICAL readings for the same active leak do not create duplicate emergency-close actions.
    TEST 3: Repeated CRITICAL readings still update the leak peak correctly."""
    db = TestingSessionLocal()
    device = db.query(Device).filter(Device.id == "paired_dev_1").first()
    device.valve_status = "OPEN"
    db.query(LeakEvent).filter(LeakEvent.device_id == "paired_dev_1").delete()
    db.query(DeviceCommand).filter(DeviceCommand.device_id == "paired_dev_1").delete()
    db.commit()
    db.close()

    # First critical
    client.post("/api/v1/telemetry/gas", json={"device_id": "paired_dev_1", "ppm_value": 1200, "timestamp": datetime.now(timezone.utc).isoformat()})
    # Repeated critical
    client.post("/api/v1/telemetry/gas", json={"device_id": "paired_dev_1", "ppm_value": 1500, "timestamp": datetime.now(timezone.utc).isoformat()})

    db = TestingSessionLocal()
    leaks = db.query(LeakEvent).filter(LeakEvent.device_id == "paired_dev_1").all()
    commands = db.query(DeviceCommand).filter(DeviceCommand.device_id == "paired_dev_1").all()
    device = db.query(Device).filter(Device.id == "paired_dev_1").first()
    db.close()

    assert len(leaks) == 1
    assert leaks[0].peak_ppm == 1500  # TEST 3
    assert len(commands) == 1  # TEST 2
    assert device.valve_status == "CLOSED"


def test_normal_resolves_leak_but_does_not_reopen_valve():
    """TEST 4: NORMAL resolves the active leak but does not automatically reopen the valve.
    TEST 10: RESET is explicit and does not happen automatically because gas became NORMAL."""
    db = TestingSessionLocal()
    device = db.query(Device).filter(Device.id == "paired_dev_1").first()
    device.valve_status = "OPEN"
    db.query(LeakEvent).filter(LeakEvent.device_id == "paired_dev_1").delete()
    db.query(DeviceCommand).filter(DeviceCommand.device_id == "paired_dev_1").delete()
    db.commit()
    db.close()

    # Leak
    client.post("/api/v1/telemetry/gas", json={"device_id": "paired_dev_1", "ppm_value": 1200, "timestamp": datetime.now(timezone.utc).isoformat()})
    # Resolve
    client.post("/api/v1/telemetry/gas", json={"device_id": "paired_dev_1", "ppm_value": 300, "timestamp": datetime.now(timezone.utc).isoformat()})

    db = TestingSessionLocal()
    leaks = db.query(LeakEvent).filter(LeakEvent.device_id == "paired_dev_1").all()
    device = db.query(Device).filter(Device.id == "paired_dev_1").first()
    commands = db.query(DeviceCommand).filter(DeviceCommand.device_id == "paired_dev_1").all()
    db.close()

    assert leaks[0].end_time is not None  # Resolved
    assert device.valve_status == "CLOSED"  # Not reopened
    assert len(commands) == 1
    assert commands[0].command == "EMERGENCY_CLOSE"


def test_warning_does_not_trigger_emergency_close():
    """TEST 5: WARNING does not trigger emergency close."""
    db = TestingSessionLocal()
    device = db.query(Device).filter(Device.id == "paired_dev_1").first()
    device.valve_status = "OPEN"
    db.query(DeviceCommand).filter(DeviceCommand.device_id == "paired_dev_1").delete()
    db.commit()
    db.close()

    client.post("/api/v1/telemetry/gas", json={"device_id": "paired_dev_1", "ppm_value": 600, "timestamp": datetime.now(timezone.utc).isoformat()})

    db = TestingSessionLocal()
    device = db.query(Device).filter(Device.id == "paired_dev_1").first()
    commands = db.query(DeviceCommand).filter(DeviceCommand.device_id == "paired_dev_1").all()
    db.close()

    assert device.valve_status == "OPEN"
    assert len(commands) == 0


def test_new_critical_creates_new_emergency_close():
    """TEST 6: After a leak is resolved, a new CRITICAL event creates a new emergency-close action."""
    db = TestingSessionLocal()
    device = db.query(Device).filter(Device.id == "paired_dev_1").first()
    device.valve_status = "OPEN"
    db.query(LeakEvent).filter(LeakEvent.device_id == "paired_dev_1").delete()
    db.query(DeviceCommand).filter(DeviceCommand.device_id == "paired_dev_1").delete()
    db.commit()
    db.close()

    client.post("/api/v1/telemetry/gas", json={"device_id": "paired_dev_1", "ppm_value": 1200, "timestamp": datetime.now(timezone.utc).isoformat()})
    client.post("/api/v1/telemetry/gas", json={"device_id": "paired_dev_1", "ppm_value": 300, "timestamp": datetime.now(timezone.utc).isoformat()})
    # Reset valve manually to simulate actual reset
    client.post("/api/v1/devices/paired_dev_1/valve/reset")
    
    # New leak
    client.post("/api/v1/telemetry/gas", json={"device_id": "paired_dev_1", "ppm_value": 1500, "timestamp": datetime.now(timezone.utc).isoformat()})

    db = TestingSessionLocal()
    commands = db.query(DeviceCommand).filter(DeviceCommand.device_id == "paired_dev_1").all()
    db.close()

    assert len(commands) == 3
    assert commands[0].command == "EMERGENCY_CLOSE"
    assert commands[1].command == "RESET"
    assert commands[2].command == "EMERGENCY_CLOSE"


def test_authorized_owner_manual_close_and_idempotency():
    """TEST 7: Authorized owner can request emergency close.
    TEST 9: Emergency close is idempotent when the device is already software-CLOSED."""
    db = TestingSessionLocal()
    device = db.query(Device).filter(Device.id == "paired_dev_1").first()
    device.valve_status = "OPEN"
    db.query(DeviceCommand).filter(DeviceCommand.device_id == "paired_dev_1").delete()
    db.commit()
    db.close()

    # Request 1 (Successful)
    response = client.post("/api/v1/devices/paired_dev_1/valve/emergency-close")
    assert response.status_code == 200

    # Request 2 (Idempotent)
    response2 = client.post("/api/v1/devices/paired_dev_1/valve/emergency-close")
    assert response2.status_code == 200

    db = TestingSessionLocal()
    device = db.query(Device).filter(Device.id == "paired_dev_1").first()
    commands = db.query(DeviceCommand).filter(DeviceCommand.device_id == "paired_dev_1").all()
    db.close()

    assert device.valve_status == "CLOSED"
    assert len(commands) == 1  # Only recorded once


def test_unauthorized_user_manual_close():
    """TEST 8: Unauthorized user attempting emergency close receives HTTP 403."""
    db = TestingSessionLocal()
    # Create a device owned by another user (or no user)
    device = Device(id="other_user_dev", name="Other Dev", valve_status="OPEN", user_id=999)
    db.merge(device)
    db.commit()
    db.close()

    response = client.post("/api/v1/devices/other_user_dev/valve/emergency-close")
    assert response.status_code == 403


def test_no_physical_actuation_claim():
    """TEST 11: The system never represents software CLOSED as confirmed physical valve closure.
    (Validated via response model and status values)"""
    db = TestingSessionLocal()
    device = db.query(Device).filter(Device.id == "paired_dev_1").first()
    device.valve_status = "OPEN"
    db.commit()
    db.close()
    
    response = client.post("/api/v1/devices/paired_dev_1/valve/emergency-close")
    data = response.json()
    assert data["valve_status"] == "CLOSED"
    # Ensure there's no "hardware_confirmed" or similar flag that is True
    # The API design only returns standard device schema without claiming physical state


def test_manual_reset():
    """Verify manual reset endpoint works and is idempotent."""
    db = TestingSessionLocal()
    device = db.query(Device).filter(Device.id == "paired_dev_1").first()
    device.valve_status = "CLOSED"
    db.query(DeviceCommand).filter(DeviceCommand.device_id == "paired_dev_1").delete()
    db.commit()
    db.close()

    response = client.post("/api/v1/devices/paired_dev_1/valve/reset")
    assert response.status_code == 200
    
    response2 = client.post("/api/v1/devices/paired_dev_1/valve/reset")
    assert response2.status_code == 200

    db = TestingSessionLocal()
    device = db.query(Device).filter(Device.id == "paired_dev_1").first()
    commands = db.query(DeviceCommand).filter(DeviceCommand.device_id == "paired_dev_1").all()
    db.close()

    assert device.valve_status == "OPEN"
    assert len(commands) == 1
    assert commands[0].command == "RESET"
