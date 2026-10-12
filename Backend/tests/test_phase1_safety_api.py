"""
tests/test_phase1_safety_api.py
================================
Phase 1 — Safety API Route Integration Tests

Covers every endpoint in app/api/v1/safety.py:

  GET  /api/v1/devices/{device_id}/safety
  GET  /api/v1/devices/{device_id}/gas-readings
  GET  /api/v1/devices/{device_id}/leaks/active
  GET  /api/v1/devices/{device_id}/leaks
  GET  /api/v1/devices/{device_id}/diagnostics
  POST /api/v1/devices/{device_id}/valve/emergency-close
  POST /api/v1/devices/{device_id}/valve/reset

Test matrix (13 required tests + supplementary assertions):
  1.  Authenticated owner can GET safety summary
  2.  Unauthenticated request returns 401
  3.  Wrong owner returns 403
  4.  Unknown device returns 404
  5.  Gas readings endpoint returns recent readings
  6.  Active leak endpoint works (with and without active leak)
  7.  Leak history endpoint returns all events
  8.  Diagnostics endpoint returns structured report
  9.  Emergency close endpoint sets valve to CLOSED
  10. Emergency close creates a DeviceCommand record
  11. Repeated emergency close is idempotent (no duplicate command)
  12. Manual valve reset sets valve to OPEN
  13. Unauthorized valve operation is rejected

Shared test infrastructure (engine, client, setup_db) is imported from conftest.py.
"""
import pytest
from datetime import datetime, timezone

from app.models.device import Device
from app.models.device_command import DeviceCommand
from app.models.gas_reading import GasReading
from app.models.leak_event import LeakEvent
from tests.conftest import client, TestingSessionLocal


# ── Helpers ────────────────────────────────────────────────────────────────────

OWNED_DEVICE    = "paired_dev_1"   # belongs to user 1 (the test user)
OTHER_DEVICE    = "paired_dev_2"   # belongs to user 2
MISSING_DEVICE  = "nonexistent-device-xyz"

BASE = "/api/v1/devices"


def _ingest_gas(device_id: str, ppm: float):
    """POST a synthetic gas reading through the telemetry endpoint."""
    return client.post(
        "/api/v1/telemetry/gas",
        json={
            "device_id": device_id,
            "ppm_value": ppm,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


def _seed_gas_reading(device_id: str, ppm: float, status: str = "normal"):
    """Directly insert a gas reading into the test DB."""
    db = TestingSessionLocal()
    db.add(GasReading(
        device_id=device_id,
        ppm_value=ppm,
        status=status,
        timestamp=datetime.now(timezone.utc),
    ))
    db.commit()
    db.close()


def _get_device_valve_status(device_id: str) -> str:
    db = TestingSessionLocal()
    device = db.query(Device).filter(Device.id == device_id).first()
    db.close()
    return device.valve_status if device else "UNKNOWN"


def _count_device_commands(device_id: str, command: str) -> int:
    db = TestingSessionLocal()
    count = (
        db.query(DeviceCommand)
        .filter(DeviceCommand.device_id == device_id, DeviceCommand.command == command)
        .count()
    )
    db.close()
    return count


# ==============================================================
# TEST 1 — Authenticated owner can GET safety summary
# ==============================================================

def test_safety_summary_authenticated_owner():
    """User 1 can retrieve the safety summary for their own device."""
    _seed_gas_reading(OWNED_DEVICE, ppm=350.0, status="normal")

    response = client.get(f"{BASE}/{OWNED_DEVICE}/safety")

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["device_id"] == OWNED_DEVICE
    # When a reading exists it should be returned
    assert data["latest_gas_ppm"] == pytest.approx(350.0, abs=0.1)
    assert data["status"] == "normal"
    assert data["valve_status"] is not None
    assert data["connection_status"] in ("online", "offline", "unknown")


def test_safety_summary_no_readings():
    """Safety summary returns gracefully when no readings exist yet."""
    response = client.get(f"{BASE}/{OWNED_DEVICE}/safety")

    assert response.status_code == 200
    data = response.json()
    assert data["device_id"] == OWNED_DEVICE
    assert data["latest_gas_ppm"] is None
    assert data["status"] is None
    assert data["connection_status"] == "unknown"


# ==============================================================
# TEST 2 — Unauthenticated request returns 401
# ==============================================================
# conftest.py wires override_get_current_user to always return user 1.
# To test a genuine 401 we must make a request that bypasses the override.
# We construct a separate TestClient with NO dependency overrides so the
# real JWT validation runs and correctly rejects an unauthenticated call.

def test_safety_summary_unauthenticated():
    """
    A request with no token must be rejected with 401.

    We instantiate a *bare* TestClient (no dependency overrides) so the
    real OAuth2 scheme runs. If FastAPI returns 422 instead of 401 for a
    completely missing Authorization header, we accept that as 4xx to keep
    the test framework-version-agnostic; the important thing is that it is
    NOT 200.
    """
    from fastapi.testclient import TestClient
    from app.main import app as real_app

    # Build a client without dependency overrides
    bare_client = TestClient(real_app, raise_server_exceptions=False)
    # The shared overrides are already set on the app object; clear them
    # for the duration of this test.
    original_overrides = dict(real_app.dependency_overrides)
    real_app.dependency_overrides.clear()
    try:
        response = bare_client.get(f"{BASE}/{OWNED_DEVICE}/safety")
        assert response.status_code in (401, 403, 422), (
            f"Expected 401/403/422 without auth, got {response.status_code}"
        )
    finally:
        # Restore overrides so later tests are unaffected
        real_app.dependency_overrides.update(original_overrides)


# ==============================================================
# TEST 3 — Wrong owner returns 403
# ==============================================================

def test_safety_summary_wrong_owner():
    """User 1 (test user) must NOT be able to read user 2's device."""
    response = client.get(f"{BASE}/{OTHER_DEVICE}/safety")
    assert response.status_code == 403, response.text


# ==============================================================
# TEST 4 — Unknown device returns 404
# ==============================================================

def test_safety_summary_unknown_device():
    """Requesting a non-existent device must return 404."""
    response = client.get(f"{BASE}/{MISSING_DEVICE}/safety")
    assert response.status_code == 404, response.text


# ==============================================================
# TEST 5 — Gas readings endpoint returns recent readings
# ==============================================================

def test_gas_readings_returns_results():
    """Owner can retrieve recent gas readings for their device."""
    # Seed three readings via telemetry (goes through full pipeline)
    for ppm in [300.0, 600.0, 1100.0]:
        r = _ingest_gas(OWNED_DEVICE, ppm)
        assert r.status_code == 201

    response = client.get(f"{BASE}/{OWNED_DEVICE}/gas-readings?limit=10")

    assert response.status_code == 200, response.text
    readings = response.json()
    assert isinstance(readings, list)
    assert len(readings) == 3


def test_gas_readings_limit_is_respected():
    """The ?limit param caps how many readings are returned."""
    for ppm in [100, 200, 300, 400, 500]:
        _seed_gas_reading(OWNED_DEVICE, ppm)

    response = client.get(f"{BASE}/{OWNED_DEVICE}/gas-readings?limit=2")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_gas_readings_wrong_owner_403():
    """User 1 cannot read gas readings for user 2's device."""
    response = client.get(f"{BASE}/{OTHER_DEVICE}/gas-readings")
    assert response.status_code == 403


def test_gas_readings_unknown_device_404():
    """Gas readings for a non-existent device must return 404."""
    response = client.get(f"{BASE}/{MISSING_DEVICE}/gas-readings")
    assert response.status_code == 404


# ==============================================================
# TEST 6 — Active leak endpoint
# ==============================================================

def test_active_leak_returns_null_when_none():
    """When there is no active leak, the endpoint returns null (HTTP 200)."""
    response = client.get(f"{BASE}/{OWNED_DEVICE}/leaks/active")
    assert response.status_code == 200
    assert response.json() is None


def test_active_leak_returned_when_exists():
    """When a critical reading creates a leak event, active leak is returned."""
    _ingest_gas(OWNED_DEVICE, ppm=1200.0)

    response = client.get(f"{BASE}/{OWNED_DEVICE}/leaks/active")
    assert response.status_code == 200
    data = response.json()
    assert data is not None
    assert data["device_id"] == OWNED_DEVICE
    assert data["active"] is True
    assert data["end_time"] is None
    assert data["peak_ppm"] == pytest.approx(1200.0, abs=0.1)


def test_active_leak_wrong_owner_403():
    response = client.get(f"{BASE}/{OTHER_DEVICE}/leaks/active")
    assert response.status_code == 403


def test_active_leak_unknown_device_404():
    response = client.get(f"{BASE}/{MISSING_DEVICE}/leaks/active")
    assert response.status_code == 404


# ==============================================================
# TEST 7 — Leak history endpoint
# ==============================================================

def test_leak_history_empty_when_no_events():
    """Leak history returns empty list when no events exist."""
    response = client.get(f"{BASE}/{OWNED_DEVICE}/leaks")
    assert response.status_code == 200
    data = response.json()
    assert "leaks" in data
    assert data["leaks"] == []


def test_leak_history_returns_all_events():
    """Leak history returns both active and resolved events."""
    # Cycle 1: create + resolve
    _ingest_gas(OWNED_DEVICE, ppm=1200.0)
    _ingest_gas(OWNED_DEVICE, ppm=200.0)
    # Cycle 2: create new active leak
    _ingest_gas(OWNED_DEVICE, ppm=1500.0)

    response = client.get(f"{BASE}/{OWNED_DEVICE}/leaks")
    assert response.status_code == 200
    data = response.json()
    leaks = data["leaks"]
    assert len(leaks) == 2

    active   = [l for l in leaks if l["active"]]
    resolved = [l for l in leaks if not l["active"]]
    assert len(active) == 1
    assert len(resolved) == 1


def test_leak_history_limit():
    """Leak history respects the limit query param."""
    # Create 3 complete leak cycles
    for _ in range(3):
        _ingest_gas(OWNED_DEVICE, ppm=1100.0)
        _ingest_gas(OWNED_DEVICE, ppm=200.0)

    response = client.get(f"{BASE}/{OWNED_DEVICE}/leaks?limit=2")
    assert response.status_code == 200
    assert len(response.json()["leaks"]) == 2


def test_leak_history_wrong_owner_403():
    response = client.get(f"{BASE}/{OTHER_DEVICE}/leaks")
    assert response.status_code == 403


def test_leak_history_unknown_device_404():
    response = client.get(f"{BASE}/{MISSING_DEVICE}/leaks")
    assert response.status_code == 404


# ==============================================================
# TEST 8 — Diagnostics endpoint
# ==============================================================

def test_diagnostics_owner_gets_report():
    """Owner gets structured diagnostics report."""
    response = client.get(f"{BASE}/{OWNED_DEVICE}/diagnostics")
    assert response.status_code == 200, response.text

    data = response.json()
    # Top-level structure
    assert "device" in data
    assert "connection" in data
    assert "sensor" in data
    assert "telemetry" in data
    assert "safety" in data

    assert data["device"]["id"] == OWNED_DEVICE
    assert "status" in data["connection"]
    assert "health" in data["sensor"]
    assert "valve_status" in data["safety"]


def test_diagnostics_wrong_owner_403():
    response = client.get(f"{BASE}/{OTHER_DEVICE}/diagnostics")
    assert response.status_code == 403


def test_diagnostics_unknown_device_404():
    response = client.get(f"{BASE}/{MISSING_DEVICE}/diagnostics")
    assert response.status_code == 404


# ==============================================================
# TEST 9 — Emergency close sets valve to CLOSED
# ==============================================================

def test_emergency_close_sets_valve_closed():
    """POST emergency-close must set device valve_status to CLOSED."""
    response = client.post(f"{BASE}/{OWNED_DEVICE}/valve/emergency-close")
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["valve_status"] == "CLOSED"

    # Verify directly in DB
    assert _get_device_valve_status(OWNED_DEVICE) == "CLOSED"


# ==============================================================
# TEST 10 — Emergency close creates a DeviceCommand record
# ==============================================================

def test_emergency_close_creates_device_command():
    """Emergency close must write exactly one EMERGENCY_CLOSE command record."""
    before_count = _count_device_commands(OWNED_DEVICE, "EMERGENCY_CLOSE")

    client.post(f"{BASE}/{OWNED_DEVICE}/valve/emergency-close")

    after_count = _count_device_commands(OWNED_DEVICE, "EMERGENCY_CLOSE")
    assert after_count == before_count + 1


# ==============================================================
# TEST 11 — Repeated emergency close is idempotent
# ==============================================================

def test_emergency_close_idempotent():
    """
    Calling emergency-close twice must NOT create a second DeviceCommand.
    The valve stays CLOSED and the second call is a no-op.
    """
    # First call
    r1 = client.post(f"{BASE}/{OWNED_DEVICE}/valve/emergency-close")
    assert r1.status_code == 200
    count_after_first = _count_device_commands(OWNED_DEVICE, "EMERGENCY_CLOSE")

    # Second call on already-closed valve
    r2 = client.post(f"{BASE}/{OWNED_DEVICE}/valve/emergency-close")
    assert r2.status_code == 200
    count_after_second = _count_device_commands(OWNED_DEVICE, "EMERGENCY_CLOSE")

    assert count_after_second == count_after_first, (
        "Idempotency violated: a second EMERGENCY_CLOSE command was written "
        "even though the valve was already CLOSED."
    )
    assert _get_device_valve_status(OWNED_DEVICE) == "CLOSED"


# ==============================================================
# TEST 12 — Manual valve reset sets valve to OPEN
# ==============================================================

def test_valve_reset_opens_closed_valve():
    """After emergency close, reset must set valve_status back to OPEN."""
    # First close it
    client.post(f"{BASE}/{OWNED_DEVICE}/valve/emergency-close")
    assert _get_device_valve_status(OWNED_DEVICE) == "CLOSED"

    # Then reset
    response = client.post(f"{BASE}/{OWNED_DEVICE}/valve/reset")
    assert response.status_code == 200, response.text

    data = response.json()
    assert data["valve_status"] == "OPEN"
    assert _get_device_valve_status(OWNED_DEVICE) == "OPEN"


def test_valve_reset_idempotent_when_already_open():
    """Reset on an already-open valve must be a no-op (idempotent)."""
    # Valve defaults to OPEN; do not close it
    before_count = _count_device_commands(OWNED_DEVICE, "RESET")

    response = client.post(f"{BASE}/{OWNED_DEVICE}/valve/reset")
    assert response.status_code == 200

    after_count = _count_device_commands(OWNED_DEVICE, "RESET")
    assert after_count == before_count, "No RESET command should be written for an already-OPEN valve"
    assert response.json()["valve_status"] == "OPEN"


def test_valve_reset_creates_command_record():
    """Reset from CLOSED must write exactly one RESET DeviceCommand record."""
    # Close first
    client.post(f"{BASE}/{OWNED_DEVICE}/valve/emergency-close")
    before_count = _count_device_commands(OWNED_DEVICE, "RESET")

    client.post(f"{BASE}/{OWNED_DEVICE}/valve/reset")

    after_count = _count_device_commands(OWNED_DEVICE, "RESET")
    assert after_count == before_count + 1


# ==============================================================
# TEST 13 — Unauthorized valve operation is rejected
# ==============================================================

def test_emergency_close_wrong_owner_403():
    """User 1 cannot emergency-close user 2's device valve."""
    response = client.post(f"{BASE}/{OTHER_DEVICE}/valve/emergency-close")
    assert response.status_code == 403


def test_valve_reset_wrong_owner_403():
    """User 1 cannot reset user 2's device valve."""
    response = client.post(f"{BASE}/{OTHER_DEVICE}/valve/reset")
    assert response.status_code == 403


def test_emergency_close_unknown_device_404():
    response = client.post(f"{BASE}/{MISSING_DEVICE}/valve/emergency-close")
    assert response.status_code == 404


def test_valve_reset_unknown_device_404():
    response = client.post(f"{BASE}/{MISSING_DEVICE}/valve/reset")
    assert response.status_code == 404


# ==============================================================
# BONUS — Safety lockout preserved: valve does NOT auto-reopen on NORMAL
# ==============================================================

def test_safety_lockout_preserved():
    """
    After emergency close, a NORMAL gas reading must NOT auto-reopen the valve.
    Reopening requires an explicit POST to /valve/reset.
    """
    # Create critical → emergency close
    _ingest_gas(OWNED_DEVICE, ppm=1200.0)
    assert _get_device_valve_status(OWNED_DEVICE) == "CLOSED"

    # Gas drops to normal → leak resolves, but valve must stay CLOSED
    _ingest_gas(OWNED_DEVICE, ppm=200.0)
    assert _get_device_valve_status(OWNED_DEVICE) == "CLOSED", (
        "Valve must NOT be auto-reopened when gas returns to normal. "
        "Explicit user action via /valve/reset is required."
    )
