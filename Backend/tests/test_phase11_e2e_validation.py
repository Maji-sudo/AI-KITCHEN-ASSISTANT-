import time
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_current_user
from app.services.simulator_service import simulator_service
from tests.conftest import client, TestingSessionLocal, override_get_current_user


def teardown_module():
    """Clean up any leftover simulator tasks after Phase 11 tests."""
    simulator_service.stop_simulation("paired_dev_1")
    simulator_service.stop_simulation("dev123")


# ==============================================================================
# SCENARIO A: NORMAL TELEMETRY
# ==============================================================================
def test_scenario_a_normal_telemetry():
    """Validate normal gas reading ingestion through canonical pipeline."""
    # 1. Submit normal reading (250 PPM) via manual telemetry endpoint
    res = client.post(
        "/api/v1/telemetry/manual/gas",
        json={"device_id": "paired_dev_1", "ppm_value": 250.0, "source": "MANUAL"},
    )
    assert res.status_code == 201
    reading = res.json()
    assert reading["ppm_value"] == 250.0
    assert reading["status"] == "normal"
    assert reading["source"] == "MANUAL"

    # 2. Confirm no active leak created
    res_leak = client.get("/api/v1/devices/paired_dev_1/leaks/active")
    assert res_leak.status_code == 200
    assert res_leak.json() is None

    # 3. Confirm Safety Read API reflects normal state
    res_safety = client.get("/api/v1/devices/paired_dev_1/safety")
    assert res_safety.status_code == 200
    safety_data = res_safety.json()
    assert safety_data["latest_gas_ppm"] == 250.0
    assert safety_data["status"] == "normal"
    assert safety_data["valve_status"] != "CLOSED"


# ==============================================================================
# SCENARIO B: WARNING TELEMETRY
# ==============================================================================
def test_scenario_b_warning_telemetry():
    """Validate warning gas reading (500–999 PPM) does not trigger leak/shutoff."""
    res = client.post(
        "/api/v1/telemetry/manual/gas",
        json={"device_id": "paired_dev_1", "ppm_value": 750.0},
    )
    assert res.status_code == 201
    reading = res.json()
    assert reading["ppm_value"] == 750.0
    assert reading["status"] == "warning"

    # Confirm no active leak is created by warning reading
    res_leak = client.get("/api/v1/devices/paired_dev_1/leaks/active")
    assert res_leak.status_code == 200
    assert res_leak.json() is None

    # Confirm Safety Read API status is warning
    res_safety = client.get("/api/v1/devices/paired_dev_1/safety")
    assert res_safety.status_code == 200
    assert res_safety.json()["status"] == "warning"


# ==============================================================================
# SCENARIO C: FIRST CRITICAL READING
# ==============================================================================
def test_scenario_c_first_critical_reading():
    """Validate first critical reading (≥1000 PPM) triggers complete safety chain."""
    res = client.post(
        "/api/v1/telemetry/manual/gas",
        json={"device_id": "paired_dev_1", "ppm_value": 1250.0},
    )
    assert res.status_code == 201
    assert res.json()["status"] == "critical"

    # 1. Active leak created
    res_leak = client.get("/api/v1/devices/paired_dev_1/leaks/active")
    assert res_leak.status_code == 200
    active_leak = res_leak.json()
    assert active_leak is not None
    assert active_leak["peak_ppm"] == 1250.0
    assert active_leak["auto_shutoff_triggered"] is True

    # 2. Software valve state becomes CLOSED
    res_safety = client.get("/api/v1/devices/paired_dev_1/safety")
    assert res_safety.status_code == 200
    assert res_safety.json()["valve_status"] == "CLOSED"
    assert res_safety.json()["status"] == "critical"

    # 3. Emergency notification created
    res_notif = client.get("/api/v1/notifications/")
    assert res_notif.status_code == 200
    assert any(n["channel"] == "emergency" for n in res_notif.json())


# ==============================================================================
# SCENARIO D: REPEATED CRITICAL READINGS (DEDUPLICATION)
# ==============================================================================
def test_scenario_d_repeated_critical_readings():
    """Validate leak deduplication & peak PPM update on repeated critical readings."""
    # Submit second higher critical reading (1500 PPM)
    res = client.post(
        "/api/v1/telemetry/manual/gas",
        json={"device_id": "paired_dev_1", "ppm_value": 1500.0},
    )
    assert res.status_code == 201

    # Confirm leak history still has 1 active leak with updated peak_ppm
    res_history = client.get("/api/v1/devices/paired_dev_1/leaks")
    assert res_history.status_code == 200
    leaks = res_history.json()["leaks"]
    assert len(leaks) == 1
    assert leaks[0]["peak_ppm"] == 1500.0


# ==============================================================================
# SCENARIO E: RECOVERY & NEW LEAK
# ==============================================================================
def test_scenario_e_recovery_and_new_leak():
    """Validate auto-resolution upon normal gas drop and creation of new leak on re-spike."""
    # 0. Create an active leak first (since DB is reset before each test)
    client.post(
        "/api/v1/telemetry/manual/gas",
        json={"device_id": "paired_dev_1", "ppm_value": 1300.0, "source": "MANUAL"},
    )

    # 1. Gas drops back to normal (< 500 PPM)
    res_norm = client.post(
        "/api/v1/telemetry/manual/gas",
        json={"device_id": "paired_dev_1", "ppm_value": 200.0, "source": "MANUAL"},
    )
    assert res_norm.status_code == 201

    # 2. Confirm active leak is now resolved
    res_active = client.get("/api/v1/devices/paired_dev_1/leaks/active")
    assert res_active.status_code == 200
    assert res_active.json() is None

    # 3. Confirm historical leak remains in DB with end_time populated
    res_hist = client.get("/api/v1/devices/paired_dev_1/leaks")
    assert res_hist.status_code == 200
    history = res_hist.json()["leaks"]
    assert len(history) == 1
    assert history[0]["end_time"] is not None

    # 4. Re-spike to critical (1400 PPM) -> New leak event created
    res_crit2 = client.post(
        "/api/v1/telemetry/manual/gas",
        json={"device_id": "paired_dev_1", "ppm_value": 1400.0, "source": "MANUAL"},
    )
    assert res_crit2.status_code == 201

    res_active2 = client.get("/api/v1/devices/paired_dev_1/leaks/active")
    assert res_active2.status_code == 200
    new_leak = res_active2.json()
    assert new_leak is not None
    assert new_leak["id"] != history[0]["id"]
    assert new_leak["peak_ppm"] == 1400.0


# ==============================================================================
# SCENARIO F: SIMULATOR END-TO-END
# ==============================================================================
def test_scenario_f_simulator_end_to_end():
    """Validate simulator lifecycle, canonical ingestion, and read API visibility."""
    simulator_service.stop_simulation("dev123")

    # 1. Get status -> not running
    res_stat1 = client.get("/api/v1/simulator/status/dev123")
    assert res_stat1.status_code == 200
    assert res_stat1.json()["running"] is False

    # 2. Start simulator
    res_start = client.post(
        "/api/v1/simulator/start",
        json={
            "device_id": "dev123",
            "baseline_ppm": 320.0,
            "interval_seconds": 0.01,
            "count": 3,
            "mode": "fluctuate",
        },
    )
    assert res_start.status_code == 200

    time.sleep(0.1)

    # 3. Verify GasReading records populated with source="SIMULATOR"
    res_readings = client.get("/api/v1/devices/dev123/gas-readings")
    assert res_readings.status_code == 200
    sim_readings = [r for r in res_readings.json() if r.get("source") == "SIMULATOR"]
    assert len(sim_readings) >= 3

    # 4. Stop simulator
    res_stop = client.post("/api/v1/simulator/stop", json={"device_id": "dev123"})
    assert res_stop.status_code == 200
    assert res_stop.json()["status"]["running"] is False


# ==============================================================================
# SIMULATOR CRITICAL SCENARIO
# ==============================================================================
def test_simulator_critical_scenario():
    """Validate simulated critical PPM triggers downstream safety pipeline via canonical service."""
    simulator_service.stop_simulation("dev123")

    # Start simulator with critical baseline (1150 PPM)
    client.post(
        "/api/v1/simulator/start",
        json={
            "device_id": "dev123",
            "baseline_ppm": 1150.0,
            "interval_seconds": 0.01,
            "count": 1,
        },
    )
    time.sleep(0.08)

    # Active leak created for dev123
    res_leak = client.get("/api/v1/devices/dev123/leaks/active")
    assert res_leak.status_code == 200
    active_leak = res_leak.json()
    assert active_leak is not None
    assert active_leak["device_id"] == "dev123"
    assert active_leak["peak_ppm"] >= 1000.0


# ==============================================================================
# OWNERSHIP & SECURITY VALIDATION
# ==============================================================================
def test_ownership_and_security():
    """Validate authentication and device ownership security barriers across safety endpoints."""
    # 1. Unauthenticated request to safety endpoint returns 401
    app.dependency_overrides.pop(get_current_user, None)
    try:
        unauth_client = TestClient(app)
        res_unauth = unauth_client.get("/api/v1/devices/paired_dev_1/safety")
        assert res_unauth.status_code == 401
    finally:
        app.dependency_overrides[get_current_user] = override_get_current_user

    # 2. Accessing another user's device (paired_dev_2) returns 403 Forbidden
    res_other = client.get("/api/v1/devices/paired_dev_2/safety")
    assert res_other.status_code == 403

    # 3. Emergency valve command on another user's device returns 403 Forbidden
    res_valve_other = client.post("/api/v1/devices/paired_dev_2/valve/emergency-close")
    assert res_valve_other.status_code == 403

    # 4. Simulator control on another user's device returns 403 Forbidden
    res_sim_other = client.post("/api/v1/simulator/start", json={"device_id": "paired_dev_2"})
    assert res_sim_other.status_code == 403

    # 5. Manual telemetry ingestion on unpaired device returns 403 Forbidden
    res_unpaired = client.post("/api/v1/telemetry/manual/gas", json={"device_id": "unpaired_dev_1", "ppm_value": 300.0})
    assert res_unpaired.status_code == 403
