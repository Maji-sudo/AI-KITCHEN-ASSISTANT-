# tests/test_safety_module.py
"""
Phase 1 + Phase 3 — Safety Module Integration Tests

Covers:
  - Unpaired-device rejection (Phase 1)
  - Paired-device acceptance (Phase 1)
  - Cross-user read authorisation (Phase 1)
  - Leak Event state machine (Phase 3)
      • CRITICAL creates LeakEvent
      • Subsequent CRITICAL updates peak_ppm (no duplicates)
      • NORMAL auto-resolves the active LeakEvent

Shared fixtures (engine, TestingSessionLocal, client, setup_db) live in conftest.py.
"""
import pytest
from datetime import datetime, timezone

from app.models.leak_event import LeakEvent
from tests.conftest import client, TestingSessionLocal  # shared fixtures


# ── Phase 1 ──────────────────────────────────────────────────────────────────

def test_telemetry_ingestion_unpaired_device():
    """Unpaired device must be rejected with 403."""
    response = client.post(
        "/api/v1/telemetry/gas",
        json={
            "device_id": "unpaired_dev_1",
            "ppm_value": 400,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert response.status_code == 403
    assert "not paired" in response.json()["detail"]


def test_telemetry_ingestion_paired_device():
    """Paired device must be accepted with 201."""
    response = client.post(
        "/api/v1/telemetry/gas",
        json={
            "device_id": "paired_dev_1",
            "ppm_value": 400,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
    assert response.status_code == 201


def test_telemetry_get_readings_unauthorized():
    """User 1 must NOT be able to read User 2's device data."""
    response = client.get("/api/v1/telemetry/gas/paired_dev_2")
    assert response.status_code == 403
    assert "Unauthorized" in response.json()["detail"]


def test_telemetry_get_readings_authorized():
    """User 1 must be able to read their own device data."""
    response = client.get("/api/v1/telemetry/gas/paired_dev_1")
    assert response.status_code == 200


# ── Phase 3: Leak Event State Machine ────────────────────────────────────────

def test_critical_creates_leak_event():
    """First CRITICAL reading creates exactly one LeakEvent."""
    client.post(
        "/api/v1/telemetry/gas",
        json={"device_id": "paired_dev_1", "ppm_value": 1200,
              "timestamp": datetime.now(timezone.utc).isoformat()},
    )
    db = TestingSessionLocal()
    leaks = db.query(LeakEvent).filter(LeakEvent.device_id == "paired_dev_1").all()
    db.close()
    assert len(leaks) == 1
    assert leaks[0].peak_ppm == 1200
    assert leaks[0].end_time is None


def test_subsequent_critical_updates_peak_no_duplicate():
    """Second CRITICAL at higher PPM updates peak_ppm; no new LeakEvent created."""
    # First CRITICAL
    client.post(
        "/api/v1/telemetry/gas",
        json={"device_id": "paired_dev_1", "ppm_value": 1200,
              "timestamp": datetime.now(timezone.utc).isoformat()},
    )
    # Second CRITICAL (higher)
    client.post(
        "/api/v1/telemetry/gas",
        json={"device_id": "paired_dev_1", "ppm_value": 1500,
              "timestamp": datetime.now(timezone.utc).isoformat()},
    )
    db = TestingSessionLocal()
    leaks = db.query(LeakEvent).filter(LeakEvent.device_id == "paired_dev_1").all()
    db.close()
    assert len(leaks) == 1, "No duplicate LeakEvent should be created"
    assert leaks[0].peak_ppm == 1500, "peak_ppm must be updated to the higher value"


def test_warning_does_not_create_or_resolve_leak():
    """WARNING reading must NOT create a new LeakEvent or resolve an existing one."""
    # Create an active leak first
    client.post(
        "/api/v1/telemetry/gas",
        json={"device_id": "paired_dev_1", "ppm_value": 1200,
              "timestamp": datetime.now(timezone.utc).isoformat()},
    )
    # Now send a WARNING reading
    client.post(
        "/api/v1/telemetry/gas",
        json={"device_id": "paired_dev_1", "ppm_value": 750,
              "timestamp": datetime.now(timezone.utc).isoformat()},
    )
    db = TestingSessionLocal()
    leaks = db.query(LeakEvent).filter(LeakEvent.device_id == "paired_dev_1").all()
    db.close()
    assert len(leaks) == 1, "WARNING must not create a second LeakEvent"
    assert leaks[0].end_time is None, "WARNING must not resolve the active LeakEvent"


def test_normal_auto_resolves_active_leak():
    """NORMAL reading must resolve the active LeakEvent."""
    # Create active leak
    client.post(
        "/api/v1/telemetry/gas",
        json={"device_id": "paired_dev_1", "ppm_value": 1200,
              "timestamp": datetime.now(timezone.utc).isoformat()},
    )
    # Resolve with NORMAL
    client.post(
        "/api/v1/telemetry/gas",
        json={"device_id": "paired_dev_1", "ppm_value": 300,
              "timestamp": datetime.now(timezone.utc).isoformat()},
    )
    db = TestingSessionLocal()
    leaks = db.query(LeakEvent).filter(LeakEvent.device_id == "paired_dev_1").all()
    db.close()
    assert len(leaks) == 1
    assert leaks[0].end_time is not None, "Active leak must be resolved on NORMAL reading"


def test_new_critical_after_resolution_creates_new_leak():
    """After resolution a new CRITICAL must create a brand-new LeakEvent."""
    # Cycle 1: create + resolve
    client.post(
        "/api/v1/telemetry/gas",
        json={"device_id": "paired_dev_1", "ppm_value": 1200,
              "timestamp": datetime.now(timezone.utc).isoformat()},
    )
    client.post(
        "/api/v1/telemetry/gas",
        json={"device_id": "paired_dev_1", "ppm_value": 200,
              "timestamp": datetime.now(timezone.utc).isoformat()},
    )
    # Cycle 2: new critical
    client.post(
        "/api/v1/telemetry/gas",
        json={"device_id": "paired_dev_1", "ppm_value": 2000,
              "timestamp": datetime.now(timezone.utc).isoformat()},
    )
    db = TestingSessionLocal()
    leaks = db.query(LeakEvent).filter(LeakEvent.device_id == "paired_dev_1").all()
    db.close()
    assert len(leaks) == 2, "A new LeakEvent must be created after the previous one was resolved"
    resolved = [l for l in leaks if l.end_time is not None]
    active   = [l for l in leaks if l.end_time is None]
    assert len(resolved) == 1
    assert len(active)   == 1
    assert active[0].peak_ppm == 2000


# ── Legacy full-cycle convenience test (retained for Phase 1 regression) ─────

def test_leak_deduplication_full_cycle():
    """Full CRITICAL → higher-CRITICAL → NORMAL cycle regression test."""
    db = TestingSessionLocal()

    # First critical reading
    r1 = client.post(
        "/api/v1/telemetry/gas",
        json={"device_id": "paired_dev_1", "ppm_value": 1200,
              "timestamp": datetime.now(timezone.utc).isoformat()},
    )
    assert r1.status_code == 201

    db.expire_all()
    leaks = db.query(LeakEvent).filter(LeakEvent.device_id == "paired_dev_1").all()
    assert len(leaks) == 1
    assert leaks[0].peak_ppm == 1200

    # Second critical (higher)
    r2 = client.post(
        "/api/v1/telemetry/gas",
        json={"device_id": "paired_dev_1", "ppm_value": 1500,
              "timestamp": datetime.now(timezone.utc).isoformat()},
    )
    assert r2.status_code == 201

    db.expire_all()
    leaks = db.query(LeakEvent).filter(LeakEvent.device_id == "paired_dev_1").all()
    assert len(leaks) == 1, "Deduplicated"
    assert leaks[0].peak_ppm == 1500

    # Normal reading → auto-resolve
    r3 = client.post(
        "/api/v1/telemetry/gas",
        json={"device_id": "paired_dev_1", "ppm_value": 300,
              "timestamp": datetime.now(timezone.utc).isoformat()},
    )
    assert r3.status_code == 201

    db.expire_all()
    leaks = db.query(LeakEvent).filter(LeakEvent.device_id == "paired_dev_1").all()
    assert len(leaks) == 1
    assert leaks[0].end_time is not None, "Resolved"

    db.close()
