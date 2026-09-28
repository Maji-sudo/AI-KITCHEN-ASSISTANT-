import time
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_current_user
from app.services.simulator_service import simulator_service
from tests.conftest import client, TestingSessionLocal, override_get_current_user


def teardown_module():
    """Clean up any leftover simulator tasks after tests."""
    simulator_service.stop_simulation("paired_dev_1")
    simulator_service.stop_simulation("dev123")


def test_1_start_simulator_owned_device():
    """Start simulator for owned device paired_dev_1 succeeds."""
    response = client.post(
        "/api/v1/simulator/start",
        json={
            "device_id": "paired_dev_1",
            "baseline_ppm": 300.0,
            "interval_seconds": 0.05,
            "count": 5,
            "mode": "fluctuate",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Simulator started successfully"
    assert data["status"]["device_id"] == "paired_dev_1"
    assert data["status"]["running"] is True


def test_2_start_requires_authentication():
    """Start endpoint requires authentication (returns 401 when unauthenticated)."""
    # Temporarily remove override for get_current_user to simulate unauthenticated request
    app.dependency_overrides.pop(get_current_user, None)
    try:
        unauth_client = TestClient(app)
        response = unauth_client.post(
            "/api/v1/simulator/start",
            json={"device_id": "paired_dev_1"},
        )
        assert response.status_code == 401
    finally:
        app.dependency_overrides[get_current_user] = override_get_current_user


def test_3_start_another_users_device_returns_403():
    """User 1 attempting to start simulator for user 2's device (paired_dev_2) returns 403."""
    response = client.post(
        "/api/v1/simulator/start",
        json={"device_id": "paired_dev_2", "baseline_ppm": 300.0},
    )
    assert response.status_code == 403
    assert "Unauthorized" in response.json()["detail"] or "access" in response.json()["detail"]


def test_4_unpaired_device_returns_403():
    """Attempting to start simulator for unpaired device (unpaired_dev_1) returns 403."""
    response = client.post(
        "/api/v1/simulator/start",
        json={"device_id": "unpaired_dev_1", "baseline_ppm": 300.0},
    )
    assert response.status_code == 403


def test_5_simulator_status_reports_running():
    """GET /api/v1/simulator/status returns running state and counts."""
    # Ensure simulator is started for paired_dev_1
    client.post(
        "/api/v1/simulator/start",
        json={
            "device_id": "paired_dev_1",
            "baseline_ppm": 350.0,
            "interval_seconds": 0.05,
            "count": 5,
        },
    )
    # Test path parameter endpoint
    res_path = client.get("/api/v1/simulator/status/paired_dev_1")
    assert res_path.status_code == 200
    data_path = res_path.json()
    assert data_path["device_id"] == "paired_dev_1"
    assert "running" in data_path

    # Test query parameter endpoint
    res_query = client.get("/api/v1/simulator/status?device_id=paired_dev_1")
    assert res_query.status_code == 200
    assert res_query.json()["device_id"] == "paired_dev_1"

    # Stop simulator cleanly
    client.post("/api/v1/simulator/stop", json={"device_id": "paired_dev_1"})


def test_6_7_8_simulator_generates_telemetry_source_simulator_canonical():
    """Simulator generates telemetry with source="SIMULATOR" via canonical service."""
    # Stop any previous instance
    simulator_service.stop_simulation("paired_dev_1")

    # Start 3-reading simulation
    client.post(
        "/api/v1/simulator/start",
        json={
            "device_id": "paired_dev_1",
            "baseline_ppm": 250.0,
            "interval_seconds": 0.01,
            "count": 3,
        },
    )
    time.sleep(0.1)  # Allow async background task to complete all 3 readings

    # Query gas history via Phase 7 API
    res = client.get("/api/v1/devices/paired_dev_1/gas-readings")
    assert res.status_code == 200
    readings = res.json()
    assert len(readings) >= 3

    # Check source field is SIMULATOR
    sim_readings = [r for r in readings if r.get("source") == "SIMULATOR"]
    assert len(sim_readings) >= 3
    for r in sim_readings:
        assert r["device_id"] == "paired_dev_1"
        assert r["status"] in ["normal", "warning", "critical"]


def test_9_generated_readings_appear_in_phase7_read_apis():
    """Generated telemetry appears in Phase 7 safety & leak read APIs."""
    res_safety = client.get("/api/v1/devices/paired_dev_1/safety")
    assert res_safety.status_code == 200
    safety_data = res_safety.json()
    assert safety_data["device_id"] == "paired_dev_1"
    assert safety_data["latest_gas_reading"] is not None

    res_diag = client.get("/api/v1/devices/paired_dev_1/diagnostics")
    assert res_diag.status_code == 200
    assert res_diag.json()["device_id"] == "paired_dev_1"


def test_10_simulator_produces_changing_ppm():
    """Simulator produces changing PPM values rather than static identical values."""
    simulator_service.stop_simulation("dev123")
    client.post(
        "/api/v1/simulator/start",
        json={
            "device_id": "dev123",
            "baseline_ppm": 300.0,
            "interval_seconds": 0.01,
            "count": 4,
            "mode": "increase",
        },
    )
    time.sleep(0.1)

    res = client.get("/api/v1/devices/dev123/gas-readings")
    assert res.status_code == 200
    readings = res.json()
    assert len(readings) >= 2
    ppm_values = [r["ppm_value"] for r in readings]
    # Check that not all PPM values are identical
    assert len(set(ppm_values)) > 1


def test_11_stop_simulator_stops_future_generation():
    """Stopping simulator cleanly stops future reading generation."""
    simulator_service.stop_simulation("paired_dev_1")
    
    # Start long simulator
    client.post(
        "/api/v1/simulator/start",
        json={
            "device_id": "paired_dev_1",
            "baseline_ppm": 200.0,
            "interval_seconds": 0.05,
        },
    )
    time.sleep(0.08)

    # Stop simulator
    stop_res = client.post("/api/v1/simulator/stop", json={"device_id": "paired_dev_1"})
    assert stop_res.status_code == 200
    assert stop_res.json()["status"]["running"] is False

    # Get reading count after stopping
    res1 = client.get("/api/v1/devices/paired_dev_1/gas-readings")
    count1 = len(res1.json())

    time.sleep(0.12)

    # Verify no new readings accumulated after stop
    res2 = client.get("/api/v1/devices/paired_dev_1/gas-readings")
    count2 = len(res2.json())
    assert count2 == count1


def test_12_duplicate_start_returns_409_conflict():
    """Starting simulator twice for the same device returns 409 Conflict."""
    simulator_service.stop_simulation("paired_dev_1")

    # Start first time
    res1 = client.post(
        "/api/v1/simulator/start",
        json={
            "device_id": "paired_dev_1",
            "baseline_ppm": 200.0,
            "interval_seconds": 0.5,
        },
    )
    assert res1.status_code == 200

    # Start second time while still running
    res2 = client.post(
        "/api/v1/simulator/start",
        json={
            "device_id": "paired_dev_1",
            "baseline_ppm": 200.0,
            "interval_seconds": 0.5,
        },
    )
    assert res2.status_code == 409
    assert "already running" in res2.json()["detail"]

    # Clean up
    client.post("/api/v1/simulator/stop", json={"device_id": "paired_dev_1"})


def test_13_14_simulated_critical_triggers_downstream_safety_logic():
    """
    Simulated CRITICAL reading (≥1000 PPM) reaches canonical service and triggers:
      - LeakEvent creation
      - Emergency Notification to owner
      - Emergency Close DeviceCommand
      - Valve status updated to CLOSED
    """
    simulator_service.stop_simulation("paired_dev_1")

    # Start simulator configured with CRITICAL baseline (1200 PPM)
    client.post(
        "/api/v1/simulator/start",
        json={
            "device_id": "paired_dev_1",
            "baseline_ppm": 1200.0,
            "interval_seconds": 0.01,
            "count": 1,
        },
    )
    time.sleep(0.08)

    # Check active leak API (Phase 7)
    res_leak = client.get("/api/v1/devices/paired_dev_1/leaks/active")
    assert res_leak.status_code == 200
    active_leak = res_leak.json()
    assert active_leak is not None
    assert active_leak["device_id"] == "paired_dev_1"
    assert active_leak["peak_ppm"] >= 1000.0
    assert active_leak["auto_shutoff_triggered"] is True

    # Check safety status API (Phase 7) - valve status should be CLOSED
    res_safety = client.get("/api/v1/devices/paired_dev_1/safety")
    assert res_safety.status_code == 200
    assert res_safety.json()["valve_status"] == "CLOSED"

    # Check notifications API (Phase 4)
    res_notif = client.get("/api/v1/notifications/")
    assert res_notif.status_code == 200
    notifications = res_notif.json()
    assert any(n["type"] == "EMERGENCY" for n in notifications)


def test_15_no_duplicated_safety_logic_in_simulator():
    """Verify simulator service delegates all logic to telemetry_service."""
    import inspect
    from app.services.simulator_service import SimulatorService
    
    source_code = inspect.getsource(SimulatorService)
    assert "_handle_critical_gas" not in source_code
    assert "record_leak_event" not in source_code
    assert "issue_emergency_close" not in source_code
    assert "telemetry_service.record_gas_reading" in source_code
