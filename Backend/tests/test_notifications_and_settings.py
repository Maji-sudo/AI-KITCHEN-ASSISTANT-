import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.db.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.device import Device
from app.models.notification import Notification
from app.services.notification_service import notification_service
from tests.conftest import TestingSessionLocal, override_get_current_user

client = TestClient(app)


def set_active_user(user_id: int):
    app.dependency_overrides[get_current_user] = lambda db=Depends(get_db): db.query(User).filter(User.id == user_id).first()


@pytest.fixture(autouse=True)
def restore_default_user():
    set_active_user(1)
    yield
    app.dependency_overrides[get_current_user] = override_get_current_user


# ==============================================================================
# SETTINGS & TARGET ADDRESS TESTS
# ==============================================================================

def test_get_settings_initial_state():
    """Test getting settings when no address has been set yet."""
    set_active_user(1)
    res = client.get("/api/v1/settings/")
    assert res.status_code == 200
    data = res.json()
    assert "profile" in data
    assert data["profile"]["name"] == "User 1"
    assert data["delivery_address"] is None
    assert data["notification_preferences"]["fcm_enabled"] is True
    assert data["safety_preferences"]["emergency_buzzer"] is True


def test_save_and_retrieve_target_address():
    """Scenario 1: User saves a target delivery address in Settings and retrieves it."""
    set_active_user(1)
    payload = {
        "address_line": "Flat 402, Green Glen Layout",
        "area": "Bellandur",
        "city": "Bengaluru",
        "state": "Karnataka",
        "pincode": "560103",
    }
    save_res = client.put("/api/v1/settings/address", json=payload)
    assert save_res.status_code == 200
    save_data = save_res.json()
    assert save_data["delivery_address"]["address_line"] == "Flat 402, Green Glen Layout"
    assert save_data["delivery_address"]["pincode"] == "560103"

    # Subsequent GET returns the exact saved address (persisted)
    get_res = client.get("/api/v1/settings/")
    assert get_res.status_code == 200
    addr = get_res.json()["delivery_address"]
    assert addr["address_line"] == "Flat 402, Green Glen Layout"
    assert addr["city"] == "Bengaluru"


def test_clear_target_address():
    """Scenario 4: Clearing address removes it from persistent storage."""
    set_active_user(1)
    # Ensure address exists first
    client.put("/api/v1/settings/address", json={
        "address_line": "123 Main St",
        "area": "Indiranagar",
        "city": "Bengaluru",
        "state": "Karnataka",
        "pincode": "560038"
    })

    # Clear address
    del_res = client.delete("/api/v1/settings/address")
    assert del_res.status_code == 200
    assert del_res.json()["delivery_address"] is None

    # Verify subsequent GET shows delivery_address is None
    get_res = client.get("/api/v1/settings/")
    assert get_res.status_code == 200
    assert get_res.json()["delivery_address"] is None


def test_user_isolation_for_address_and_settings():
    """Scenario 9: User 2 cannot access or mutate User 1's saved address."""
    # Save address for User 1
    set_active_user(1)
    client.put("/api/v1/settings/address", json={
        "address_line": "User 1 Secret Mansion",
        "area": "HSR",
        "city": "Bengaluru",
        "state": "Karnataka",
        "pincode": "560102"
    })

    # Switch to User 2
    set_active_user(2)
    res2 = client.get("/api/v1/settings/")
    assert res2.status_code == 200
    assert res2.json()["delivery_address"] is None


def test_update_notification_and_safety_preferences():
    """Test updating notification and safety preferences."""
    set_active_user(1)
    notif_payload = {
        "fcm_enabled": False,
        "sms_enabled": True,
        "whatsapp_enabled": False,
        "gas_leak_alerts": True,
        "cylinder_refill_reminders": True,
        "weekly_efficiency_reports": False,
        "device_offline_alerts": True,
    }
    res = client.put("/api/v1/settings/notifications", json=notif_payload)
    assert res.status_code == 200
    assert res.json()["notification_preferences"]["fcm_enabled"] is False

    safety_payload = {
        "emergency_buzzer": True,
        "auto_shutoff_enabled": True,
        "leak_sensitivity": "medium",
        "warning_threshold_ppm": 450,
    }
    safety_res = client.put("/api/v1/settings/safety", json=safety_payload)
    assert safety_res.status_code == 200
    assert safety_res.json()["safety_preferences"]["warning_threshold_ppm"] == 450


# ==============================================================================
# NOTIFICATIONS MODULE TESTS
# ==============================================================================

def test_notifications_crud_and_unread_flow():
    """Test full notifications lifecycle: create, list, mark read, unread count, delete."""
    set_active_user(1)
    db = TestingSessionLocal()
    try:
        notif = notification_service.send_emergency_alert(
            db, user_id=1, device_id="paired_dev_1", ppm_value=1250.0
        )
        assert notif.id is not None
        assert notif.user_id == 1
    finally:
        db.close()

    # Check unread count
    count_res = client.get("/api/v1/notifications/unread-count")
    assert count_res.status_code == 200
    initial_unread = count_res.json()["unread_count"]
    assert initial_unread >= 1

    # Get notifications list
    list_res = client.get("/api/v1/notifications/")
    assert list_res.status_code == 200
    notifs = list_res.json()
    assert len(notifs) >= 1
    found = next((n for n in notifs if n["id"] == notif.id), None)
    assert found is not None
    assert found["read"] is False
    assert found["payload"]["severity"] == "critical"

    # User 2 cannot see User 1's notification
    set_active_user(2)
    u2_res = client.get("/api/v1/notifications/")
    assert u2_res.status_code == 200
    u2_notifs = u2_res.json()
    assert not any(n["id"] == notif.id for n in u2_notifs)

    # User 2 cannot mark User 1's notification as read
    unauth_patch = client.patch(f"/api/v1/notifications/{notif.id}/read")
    assert unauth_patch.status_code == 404

    # Switch back to User 1
    set_active_user(1)
    read_res = client.patch(f"/api/v1/notifications/{notif.id}/read")
    assert read_res.status_code == 200
    assert read_res.json()["read"] is True

    # Mark all read
    all_read_res = client.post("/api/v1/notifications/read-all")
    assert all_read_res.status_code == 200

    # Unread count should now be 0
    count_res2 = client.get("/api/v1/notifications/unread-count")
    assert count_res2.status_code == 200
    assert count_res2.json()["unread_count"] == 0

    # Delete notification
    del_res = client.delete(f"/api/v1/notifications/{notif.id}")
    assert del_res.status_code == 200


def test_notification_deduplication():
    """Scenario 7: Duplicate notifications for same event are avoided within time window."""
    db = TestingSessionLocal()
    try:
        notif1 = notification_service.send_emergency_alert(
            db, user_id=1, device_id="paired_dev_1", ppm_value=1100.0
        )
        # Immediate repeat call for same device and user
        notif2 = notification_service.send_emergency_alert(
            db, user_id=1, device_id="paired_dev_1", ppm_value=1150.0
        )
        assert notif1.id == notif2.id
    finally:
        db.close()
