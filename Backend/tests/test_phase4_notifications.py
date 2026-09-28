import pytest
from datetime import datetime, timezone
from app.models.leak_event import LeakEvent
from app.models.notification import Notification
from tests.conftest import client, TestingSessionLocal

def test_first_critical_creates_leak_and_notification():
    """First CRITICAL reading creates exactly one LeakEvent and one emergency notification."""
    response = client.post(
        "/api/v1/telemetry/gas",
        json={"device_id": "paired_dev_1", "ppm_value": 1200, "timestamp": datetime.now(timezone.utc).isoformat()}
    )
    assert response.status_code == 201

    db = TestingSessionLocal()
    leaks = db.query(LeakEvent).filter(LeakEvent.device_id == "paired_dev_1").all()
    notifications = db.query(Notification).filter(Notification.user_id == 1).all()
    db.close()

    assert len(leaks) == 1
    assert len(notifications) == 1
    assert notifications[0].channel == "emergency"
    assert "CRITICAL GAS LEAK DETECTED" in notifications[0].payload["message"]
    assert leaks[0].notification_id == notifications[0].id
    assert notifications[0].read is False


def test_repeated_critical_does_not_create_duplicate_notifications():
    """Repeated CRITICAL readings update the same LeakEvent and do NOT create notifications."""
    db = TestingSessionLocal()
    # ensure clean state for this device's owner
    db.query(LeakEvent).filter(LeakEvent.device_id == "paired_dev_1").delete()
    db.query(Notification).filter(Notification.user_id == 1).delete()
    db.commit()
    db.close()

    for ppm in [1200, 1400, 1600]:
        client.post(
            "/api/v1/telemetry/gas",
            json={"device_id": "paired_dev_1", "ppm_value": ppm, "timestamp": datetime.now(timezone.utc).isoformat()}
        )
    
    db = TestingSessionLocal()
    leaks = db.query(LeakEvent).filter(LeakEvent.device_id == "paired_dev_1").all()
    notifications = db.query(Notification).filter(Notification.user_id == 1, Notification.channel == "emergency").all()
    db.close()

    assert len(leaks) == 1
    assert leaks[0].peak_ppm == 1600
    assert len(notifications) == 1  # No duplicate notifications


def test_normal_resolves_leak():
    """NORMAL resolves the leak without repeated resolution notifications."""
    client.post(
        "/api/v1/telemetry/gas",
        json={"device_id": "paired_dev_1", "ppm_value": 1200, "timestamp": datetime.now(timezone.utc).isoformat()}
    )
    client.post(
        "/api/v1/telemetry/gas",
        json={"device_id": "paired_dev_1", "ppm_value": 300, "timestamp": datetime.now(timezone.utc).isoformat()}
    )
    # sending second NORMAL to ensure no spam
    client.post(
        "/api/v1/telemetry/gas",
        json={"device_id": "paired_dev_1", "ppm_value": 200, "timestamp": datetime.now(timezone.utc).isoformat()}
    )
    
    db = TestingSessionLocal()
    leaks = db.query(LeakEvent).filter(LeakEvent.device_id == "paired_dev_1").all()
    db.close()

    # The leak should be resolved
    assert len(leaks) == 1
    assert leaks[0].end_time is not None


def test_new_critical_creates_new_leak_and_notification():
    """A new CRITICAL after a resolved leak creates a new LeakEvent + new notification."""
    db = TestingSessionLocal()
    # clean state
    db.query(LeakEvent).filter(LeakEvent.device_id == "paired_dev_1").delete()
    db.query(Notification).filter(Notification.user_id == 1).delete()
    db.commit()
    db.close()

    # First leak
    client.post("/api/v1/telemetry/gas", json={"device_id": "paired_dev_1", "ppm_value": 1200, "timestamp": datetime.now(timezone.utc).isoformat()})
    # Resolve
    client.post("/api/v1/telemetry/gas", json={"device_id": "paired_dev_1", "ppm_value": 300, "timestamp": datetime.now(timezone.utc).isoformat()})
    # New leak
    client.post("/api/v1/telemetry/gas", json={"device_id": "paired_dev_1", "ppm_value": 1500, "timestamp": datetime.now(timezone.utc).isoformat()})

    db = TestingSessionLocal()
    leaks = db.query(LeakEvent).filter(LeakEvent.device_id == "paired_dev_1").all()
    notifications = db.query(Notification).filter(Notification.user_id == 1, Notification.channel == "emergency").all()
    db.close()

    assert len(leaks) == 2
    assert len(notifications) == 2


def test_different_sources_trigger_notification():
    """MANUAL, SIMULATOR, and IOT continue using the same notification logic."""
    for i, source in enumerate(["MANUAL", "SIMULATOR", "IOT"]):
        device_id = f"paired_dev_1"
        client.post("/api/v1/telemetry/gas", json={"device_id": device_id, "ppm_value": 300, "source": source, "timestamp": datetime.now(timezone.utc).isoformat()}) # clear any previous
        client.post("/api/v1/telemetry/gas", json={"device_id": device_id, "ppm_value": 1200, "source": source, "timestamp": datetime.now(timezone.utc).isoformat()})
        
        db = TestingSessionLocal()
        leaks = db.query(LeakEvent).filter(LeakEvent.device_id == device_id, LeakEvent.end_time == None).all()
        assert len(leaks) == 1
        assert leaks[0].notification_id is not None
        
        client.post("/api/v1/telemetry/gas", json={"device_id": device_id, "ppm_value": 300, "source": source, "timestamp": datetime.now(timezone.utc).isoformat()})
        db.close()
