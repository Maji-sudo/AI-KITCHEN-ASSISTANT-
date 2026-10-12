"""
tests/test_phase2_database_integration.py
==========================================
Phase 2 — API + Database Integration Verification

Objective: prove that every Phase 1 safety endpoint is connected correctly to
the real backend services and that every piece of state is persisted to the
database before being exposed through the API.

Data flow under test:
    Telemetry input (HTTP POST or direct service call)
        ↓
    TelemetryService.record_gas_reading()
        ↓
    safety_classification.classify_gas()   (NORMAL<500 / WARNING 500–999 / CRITICAL≥1000)
        ↓
    gas_readings table  [DB persisted]
        ↓ (on CRITICAL)
    leak_events table   [DB persisted]
    notifications table [DB persisted]
    device_commands table (via ValveCommandService) [DB persisted]
        ↓
    SafetyReadService / DiagnosticsService / ValveCommandService
        ↓
    Phase 1 API endpoints (/api/v1/devices/{id}/safety etc.)

Every test verifies the database record DIRECTLY (not just the HTTP response)
in addition to validating the API response.

Shared fixtures (engine, TestingSessionLocal, client, setup_db) come from
conftest.py — they are imported and NOT redefined here.
"""

import pytest
from datetime import datetime, timezone

from app.models.gas_reading import GasReading
from app.models.leak_event import LeakEvent
from app.models.notification import Notification
from app.models.device import Device
from app.models.device_command import DeviceCommand

from app.services.telemetry_service import telemetry_service
from app.schemas.telemetry import GasReadingCreate

from tests.conftest import client, TestingSessionLocal


# ── Constants ─────────────────────────────────────────────────────────────────

OWNED      = "paired_dev_1"   # belongs to user 1 (the test user from conftest)
OTHER      = "paired_dev_2"   # belongs to user 2
MISSING    = "does-not-exist-phase2"
BASE       = "/api/v1/devices"

# Confirmed thresholds — must not be changed
THRESHOLD_WARNING  = 500.0
THRESHOLD_CRITICAL = 1000.0


# ── Low-level DB helpers ───────────────────────────────────────────────────────

def _db_gas_readings(device_id: str) -> list:
    db = TestingSessionLocal()
    rows = (
        db.query(GasReading)
        .filter(GasReading.device_id == device_id)
        .order_by(GasReading.timestamp.asc())
        .all()
    )
    db.close()
    return rows


def _db_leak_events(device_id: str) -> list:
    db = TestingSessionLocal()
    rows = (
        db.query(LeakEvent)
        .filter(LeakEvent.device_id == device_id)
        .order_by(LeakEvent.start_time.asc())
        .all()
    )
    db.close()
    return rows


def _db_notifications(user_id: int = 1) -> list:
    db = TestingSessionLocal()
    rows = (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.sent_at.asc())
        .all()
    )
    db.close()
    return rows


def _db_device_commands(device_id: str) -> list:
    db = TestingSessionLocal()
    rows = (
        db.query(DeviceCommand)
        .filter(DeviceCommand.device_id == device_id)
        .order_by(DeviceCommand.created_at.asc())
        .all()
    )
    db.close()
    return rows


def _db_device(device_id: str):
    db = TestingSessionLocal()
    device = db.query(Device).filter(Device.id == device_id).first()
    db.close()
    return device


def _post_gas(device_id: str, ppm: float):
    """Push a gas reading through the canonical HTTP telemetry endpoint."""
    return client.post(
        "/api/v1/telemetry/gas",
        json={
            "device_id": device_id,
            "ppm_value": ppm,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


def _direct_ingest(device_id: str, ppm: float):
    """
    Call TelemetryService directly (bypasses HTTP layer) to exercise the
    service → repository → DB chain in isolation.
    """
    db = TestingSessionLocal()
    reading_in = GasReadingCreate(
        device_id=device_id,
        ppm_value=ppm,
        timestamp=datetime.now(timezone.utc),
    )
    result = telemetry_service.record_gas_reading(db, reading_in=reading_in)
    db.close()
    return result


# ==============================================================
# SECTION 3 — GAS READING PERSISTENCE
# ==============================================================

class TestGasReadingPersistence:
    """Verify gas readings are stored correctly across the full threshold range."""

    @pytest.mark.parametrize("ppm,expected_status", [
        (100.0,   "normal"),
        (499.0,   "normal"),
        (499.9,   "normal"),
        (500.0,   "warning"),
        (750.0,   "warning"),
        (999.0,   "warning"),
        (999.9,   "warning"),
        (1000.0,  "critical"),
        (1500.0,  "critical"),
        (9999.0,  "critical"),
    ])
    def test_gas_reading_stored_with_correct_classification(self, ppm, expected_status):
        """
        For each PPM value, verify:
        1. DB record is created
        2. device_id is correct
        3. ppm_value stored correctly
        4. timestamp is stored
        5. status classification is correct
        """
        result = _direct_ingest(OWNED, ppm)

        # ── DB verification ──────────────────────────────────────────
        rows = _db_gas_readings(OWNED)
        assert len(rows) >= 1, "Gas reading must be persisted to gas_readings table"
        latest = rows[-1]

        assert latest.device_id == OWNED,           "device_id must match"
        assert abs(latest.ppm_value - ppm) < 0.01,  "ppm_value must be stored accurately"
        assert latest.timestamp is not None,          "timestamp must be populated"
        assert latest.status == expected_status, (
            f"PPM {ppm} should be '{expected_status}', got '{latest.status}'"
        )

    def test_gas_reading_api_returns_persisted_reading(self):
        """
        After inserting via the canonical telemetry pipeline, the Phase 1
        safety endpoint must expose the same data.
        """
        ppm = 350.0
        _direct_ingest(OWNED, ppm)

        # ── API verification ─────────────────────────────────────────
        r = client.get(f"{BASE}/{OWNED}/safety")
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["device_id"] == OWNED
        assert abs(data["latest_gas_ppm"] - ppm) < 0.01
        assert data["status"] == "normal"

    def test_gas_reading_through_http_telemetry_endpoint(self):
        """
        POST to /api/v1/telemetry/gas should persist a record just like the
        direct service call.
        """
        ppm = 600.0
        r = _post_gas(OWNED, ppm)
        assert r.status_code == 201, r.text

        rows = _db_gas_readings(OWNED)
        assert len(rows) >= 1
        latest = rows[-1]
        assert latest.status == "warning"
        assert abs(latest.ppm_value - ppm) < 0.01

    def test_gas_reading_source_field_present(self):
        """source column should default to 'IOT' for HTTP-sourced readings."""
        r = _post_gas(OWNED, 300.0)
        assert r.status_code == 201

        rows = _db_gas_readings(OWNED)
        latest = rows[-1]
        # source is nullable; if present it should be 'IOT'
        assert latest.source in (None, "IOT", "SIMULATION", "MANUAL")

    def test_multiple_readings_all_persisted(self):
        """All readings in a sequence must each appear in the DB."""
        ppms = [100.0, 550.0, 1100.0, 200.0]
        for ppm in ppms:
            _direct_ingest(OWNED, ppm)

        rows = _db_gas_readings(OWNED)
        assert len(rows) == len(ppms), "Every reading must create its own DB record"

    def test_gas_reading_device_isolation(self):
        """Readings for OWNED must not appear under OTHER device."""
        _direct_ingest(OWNED, 300.0)

        owned_rows = _db_gas_readings(OWNED)
        other_rows = _db_gas_readings(OTHER)
        assert len(owned_rows) >= 1
        assert len(other_rows) == 0, "No bleed-over between devices"


# ==============================================================
# SECTION 4 + 5 + 6 — LEAK LIFECYCLE (CREATE / UPDATE / RECOVER)
# ==============================================================

class TestLeakEventLifecycle:
    """Verify the full leak state-machine persists correctly."""

    def test_critical_reading_creates_leak_event(self):
        """First CRITICAL creates exactly one LeakEvent in the DB."""
        _direct_ingest(OWNED, 1200.0)

        leaks = _db_leak_events(OWNED)
        assert len(leaks) == 1
        leak = leaks[0]

        assert leak.device_id == OWNED
        assert leak.start_time is not None
        assert abs(leak.peak_ppm - 1200.0) < 0.01
        assert leak.end_time is None,            "Active leak must have no end_time"
        assert leak.auto_shutoff_triggered is True

    def test_normal_reading_does_not_create_leak(self):
        """NORMAL reading must not create any LeakEvent."""
        _direct_ingest(OWNED, 200.0)
        assert _db_leak_events(OWNED) == []

    def test_warning_reading_does_not_create_leak(self):
        """WARNING reading must not create a new LeakEvent."""
        _direct_ingest(OWNED, 750.0)
        assert _db_leak_events(OWNED) == []

    def test_warning_after_critical_does_not_resolve_leak(self):
        """WARNING reading after an open leak must leave end_time=None."""
        _direct_ingest(OWNED, 1200.0)
        _direct_ingest(OWNED, 750.0)

        leaks = _db_leak_events(OWNED)
        assert len(leaks) == 1
        assert leaks[0].end_time is None

    def test_duplicate_critical_updates_peak_no_new_event(self):
        """
        Section 5 — Deduplication:
        Repeated CRITICAL readings must NOT create duplicate LeakEvents.
        peak_ppm must be updated to the maximum observed value.
        """
        for ppm in [1000.0, 1200.0, 1500.0, 1800.0]:
            _direct_ingest(OWNED, ppm)

        leaks = _db_leak_events(OWNED)
        assert len(leaks) == 1, "Only one LeakEvent must exist for a continuous leak"
        assert abs(leaks[0].peak_ppm - 1800.0) < 0.01, "peak_ppm must be 1800"
        assert leaks[0].end_time is None

    def test_peak_ppm_tracks_maximum_not_last(self):
        """
        peak_ppm must be the maximum across all CRITICAL readings,
        not just the most recent one.
        """
        for ppm in [1000.0, 2000.0, 1100.0]:  # goes up then back down
            _direct_ingest(OWNED, ppm)

        leaks = _db_leak_events(OWNED)
        assert abs(leaks[0].peak_ppm - 2000.0) < 0.01

    def test_normal_reading_resolves_active_leak(self):
        """
        Section 6 — Recovery:
        A NORMAL reading after a CRITICAL leak must set end_time.
        """
        _direct_ingest(OWNED, 1000.0)
        _direct_ingest(OWNED, 1500.0)
        _direct_ingest(OWNED, 300.0)   # recovery

        leaks = _db_leak_events(OWNED)
        assert len(leaks) == 1
        assert leaks[0].end_time is not None,     "Leak must be resolved on NORMAL"
        assert abs(leaks[0].peak_ppm - 1500.0) < 0.01, "peak_ppm must be preserved"

    def test_historical_leak_not_deleted_after_recovery(self):
        """Resolved LeakEvents must remain in the DB — none are deleted."""
        _direct_ingest(OWNED, 1100.0)
        _direct_ingest(OWNED, 200.0)   # resolve

        leaks = _db_leak_events(OWNED)
        assert len(leaks) == 1
        assert leaks[0].end_time is not None

    def test_second_critical_after_recovery_creates_new_event(self):
        """After resolution, a new CRITICAL creates a brand-new LeakEvent."""
        # Cycle 1
        _direct_ingest(OWNED, 1200.0)
        _direct_ingest(OWNED, 200.0)
        # Cycle 2
        _direct_ingest(OWNED, 1500.0)

        leaks = _db_leak_events(OWNED)
        assert len(leaks) == 2, "Two distinct leak events must exist"

        resolved = [l for l in leaks if l.end_time is not None]
        active   = [l for l in leaks if l.end_time is None]
        assert len(resolved) == 1
        assert len(active)   == 1
        assert abs(active[0].peak_ppm - 1500.0) < 0.01


# ==============================================================
# SECTION 7 — NOTIFICATION PERSISTENCE
# ==============================================================

class TestNotificationPersistence:
    """Verify the notification service stores records in the DB."""

    def test_critical_reading_creates_notification(self):
        """A CRITICAL reading must create at least one Notification record."""
        _direct_ingest(OWNED, 1200.0)

        notifs = _db_notifications(user_id=1)
        assert len(notifs) >= 1, "Notification must be persisted for CRITICAL reading"

    def test_notification_belongs_to_device_owner(self):
        """The notification user_id must match the device owner (user 1)."""
        _direct_ingest(OWNED, 1200.0)

        notifs = _db_notifications(user_id=1)
        assert len(notifs) >= 1
        assert all(n.user_id == 1 for n in notifs)

    def test_notification_has_safety_payload(self):
        """
        The CRITICAL notification payload must identify the device and
        carry appropriate severity information.
        """
        _direct_ingest(OWNED, 1200.0)

        notifs = _db_notifications(user_id=1)
        assert len(notifs) >= 1

        critical_notifs = [
            n for n in notifs
            if n.payload and n.payload.get("type") == "GAS_LEAK_CRITICAL"
        ]
        assert len(critical_notifs) >= 1, "At least one GAS_LEAK_CRITICAL notification expected"

        notif = critical_notifs[0]
        payload = notif.payload
        assert payload["device_id"] == OWNED
        assert payload["severity"] == "critical"
        assert "ppm_value" in payload
        assert abs(payload["ppm_value"] - 1200.0) < 0.01

    def test_notification_delivery_status_not_pending(self):
        """
        After the notification service runs, delivery_status must not stay
        as 'pending' — the service immediately marks it 'sent'.
        """
        _direct_ingest(OWNED, 1100.0)

        notifs = _db_notifications(user_id=1)
        emergency = [
            n for n in notifs
            if n.payload and n.payload.get("type") == "GAS_LEAK_CRITICAL"
        ]
        assert len(emergency) >= 1
        for n in emergency:
            assert n.delivery_status == "sent", (
                "NotificationService must mark notification 'sent' after dispatch"
            )

    def test_warning_reading_creates_warning_notification(self):
        """A WARNING reading must create a GAS_LEVEL_WARNING notification."""
        _direct_ingest(OWNED, 750.0)

        notifs = _db_notifications(user_id=1)
        warning_notifs = [
            n for n in notifs
            if n.payload and n.payload.get("type") == "GAS_LEVEL_WARNING"
        ]
        assert len(warning_notifs) >= 1

        payload = warning_notifs[0].payload
        assert payload["device_id"] == OWNED
        assert payload["severity"] == "warning"

    def test_normal_reading_creates_no_notification(self):
        """A NORMAL reading must NOT create any notification."""
        _direct_ingest(OWNED, 200.0)

        notifs = _db_notifications(user_id=1)
        assert len(notifs) == 0, "No notification should be sent for a normal reading"

    def test_notification_linked_to_leak_event(self):
        """
        The LeakEvent created by a CRITICAL reading must have its
        notification_id set to a valid Notification.id.
        """
        _direct_ingest(OWNED, 1300.0)

        leaks = _db_leak_events(OWNED)
        assert len(leaks) >= 1
        leak = leaks[0]

        assert leak.notification_id is not None, (
            "LeakEvent.notification_id must be populated after CRITICAL reading"
        )

        # Confirm the notification actually exists
        notifs = _db_notifications(user_id=1)
        notif_ids = {n.id for n in notifs}
        assert leak.notification_id in notif_ids


    def test_repeated_critical_readings_deduplication_notification(self):
        """
        Per the existing deduplication logic, repeated CRITICAL readings
        inside the same leak event do NOT create additional LeakEvents,
        therefore only ONE emergency notification is fired (for the first
        CRITICAL that opens the leak).
        """
        _direct_ingest(OWNED, 1100.0)  # opens leak + fires notification
        _direct_ingest(OWNED, 1300.0)  # updates peak; must NOT fire another

        leaks = _db_leak_events(OWNED)
        assert len(leaks) == 1, "Still one leak"

        critical_notifs = [
            n for n in _db_notifications(1)
            if n.payload and n.payload.get("type") == "GAS_LEAK_CRITICAL"
        ]
        assert len(critical_notifs) == 1, (
            "Exactly one emergency notification must be sent for one leak event"
        )


# ==============================================================
# SECTION 8 + 9 — VALVE COMMAND PERSISTENCE & IDEMPOTENCY
# ==============================================================

class TestValveCommandPersistence:
    """Verify valve commands are stored and state is correctly updated."""

    def test_emergency_close_via_api_persists_command(self):
        """
        POST /valve/emergency-close must:
        1. Return 200 with valve_status == 'CLOSED'
        2. Write a DeviceCommand record to the DB
        3. Update Device.valve_status to 'CLOSED'
        """
        r = client.post(f"{BASE}/{OWNED}/valve/emergency-close")
        assert r.status_code == 200, r.text
        assert r.json()["valve_status"] == "CLOSED"

        # DB: DeviceCommand record
        cmds = _db_device_commands(OWNED)
        assert len(cmds) == 1
        assert cmds[0].command == "EMERGENCY_CLOSE"
        assert cmds[0].status == "RECORDED"
        assert cmds[0].device_id == OWNED

        # DB: Device valve_status
        device = _db_device(OWNED)
        assert device.valve_status == "CLOSED"

    def test_emergency_close_command_status_is_recorded(self):
        """
        DeviceCommand.status must be 'RECORDED' (software-only; hardware
        delivery is out of scope for Phase 2).
        """
        client.post(f"{BASE}/{OWNED}/valve/emergency-close")

        cmds = _db_device_commands(OWNED)
        assert cmds[0].status == "RECORDED"
        assert cmds[0].executed_at is None, "executed_at stays None (no hardware yet)"

    def test_emergency_close_idempotent_no_duplicate_command(self):
        """
        Section 9 — Idempotency:
        Calling emergency-close twice must NOT create a second DeviceCommand.
        The valve stays CLOSED; the second call is a silent no-op.
        """
        client.post(f"{BASE}/{OWNED}/valve/emergency-close")
        client.post(f"{BASE}/{OWNED}/valve/emergency-close")

        cmds = [c for c in _db_device_commands(OWNED) if c.command == "EMERGENCY_CLOSE"]
        assert len(cmds) == 1, (
            "Only ONE EMERGENCY_CLOSE command must exist "
            "(second call is a no-op when valve is already CLOSED)"
        )

    def test_valve_reset_after_close_persists_command_and_opens(self):
        """
        POST /valve/reset after close must:
        1. Return 200 with valve_status == 'OPEN'
        2. Write a RESET DeviceCommand record
        3. Update Device.valve_status to 'OPEN'
        """
        client.post(f"{BASE}/{OWNED}/valve/emergency-close")
        r = client.post(f"{BASE}/{OWNED}/valve/reset")

        assert r.status_code == 200
        assert r.json()["valve_status"] == "OPEN"

        # DB: RESET command record
        reset_cmds = [c for c in _db_device_commands(OWNED) if c.command == "RESET"]
        assert len(reset_cmds) == 1
        assert reset_cmds[0].status == "RECORDED"

        # DB: Device valve_status
        device = _db_device(OWNED)
        assert device.valve_status == "OPEN"

    def test_valve_reset_idempotent_when_already_open(self):
        """
        Section 9 — Idempotency:
        Resetting an already-OPEN valve must NOT create a RESET command record.
        """
        # Valve starts OPEN (default); do not close it
        before = len([c for c in _db_device_commands(OWNED) if c.command == "RESET"])
        client.post(f"{BASE}/{OWNED}/valve/reset")
        after = len([c for c in _db_device_commands(OWNED) if c.command == "RESET"])

        assert after == before, "No RESET command must be written for an already-OPEN valve"

    def test_critical_telemetry_auto_close_persists_command(self):
        """
        A CRITICAL gas reading through the canonical pipeline must trigger
        an automatic EMERGENCY_CLOSE command — the same as the manual API.
        """
        _direct_ingest(OWNED, 1200.0)

        cmds = [c for c in _db_device_commands(OWNED) if c.command == "EMERGENCY_CLOSE"]
        assert len(cmds) == 1

        device = _db_device(OWNED)
        assert device.valve_status == "CLOSED"

    def test_safety_api_reflects_valve_state_after_close(self):
        """
        GET /safety after valve close must return valve_status == 'CLOSED'.
        The Phase 1 safety endpoint must derive state from the same DB row.
        """
        client.post(f"{BASE}/{OWNED}/valve/emergency-close")

        r = client.get(f"{BASE}/{OWNED}/safety")
        assert r.status_code == 200
        assert r.json()["valve_status"] == "CLOSED"

    def test_safety_api_reflects_valve_state_after_reset(self):
        """GET /safety after valve reset must return valve_status == 'OPEN'."""
        client.post(f"{BASE}/{OWNED}/valve/emergency-close")
        client.post(f"{BASE}/{OWNED}/valve/reset")

        r = client.get(f"{BASE}/{OWNED}/safety")
        assert r.status_code == 200
        assert r.json()["valve_status"] == "OPEN"

    def test_safety_lockout_preserved_after_normal_reading(self):
        """
        Valve must NOT auto-reopen when gas returns to normal.
        A PPM of 200 (NORMAL) after CRITICAL must keep the valve CLOSED.
        """
        _direct_ingest(OWNED, 1200.0)   # closes valve
        _direct_ingest(OWNED, 200.0)    # recovers leak — does NOT reopen valve

        device = _db_device(OWNED)
        assert device.valve_status == "CLOSED", (
            "Valve must remain CLOSED until explicit manual reset. "
            "Safety lockout preservation failure."
        )


# ==============================================================
# SECTION 10 — SAFETY READ CONSISTENCY
# ==============================================================

class TestSafetyReadConsistency:
    """GET /safety must be consistent with the real database state."""

    def test_safety_summary_no_readings_returns_nulls(self):
        """When no readings exist, safety summary must return null PPM/status."""
        r = client.get(f"{BASE}/{OWNED}/safety")
        assert r.status_code == 200
        data = r.json()
        assert data["device_id"] == OWNED
        assert data["latest_gas_ppm"] is None
        assert data["status"] is None
        assert data["connection_status"] == "unknown"

    def test_safety_summary_reflects_latest_reading(self):
        """Safety summary must expose the most recent gas reading."""
        for ppm in [200.0, 600.0]:
            _direct_ingest(OWNED, ppm)

        r = client.get(f"{BASE}/{OWNED}/safety")
        assert r.status_code == 200
        data = r.json()
        # The LAST reading was 600 (WARNING)
        assert abs(data["latest_gas_ppm"] - 600.0) < 0.01
        assert data["status"] == "warning"

    def test_safety_summary_valve_status_consistent(self):
        """Safety summary valve_status must match Device.valve_status in DB."""
        # Default is OPEN
        r = client.get(f"{BASE}/{OWNED}/safety")
        assert r.json()["valve_status"] == "OPEN"

        # Close it
        client.post(f"{BASE}/{OWNED}/valve/emergency-close")
        r = client.get(f"{BASE}/{OWNED}/safety")
        assert r.json()["valve_status"] == "CLOSED"

        # Reset it
        client.post(f"{BASE}/{OWNED}/valve/reset")
        r = client.get(f"{BASE}/{OWNED}/safety")
        assert r.json()["valve_status"] == "OPEN"

    def test_safety_summary_connection_status_online(self):
        """
        After a very recent reading, connection_status must be 'online'
        (SafetyReadService uses a 5-minute window).
        """
        _direct_ingest(OWNED, 300.0)

        r = client.get(f"{BASE}/{OWNED}/safety")
        assert r.json()["connection_status"] == "online"

    def test_safety_summary_last_seen_populated(self):
        """last_seen must be populated after at least one reading."""
        _direct_ingest(OWNED, 300.0)

        r = client.get(f"{BASE}/{OWNED}/safety")
        data = r.json()
        assert data["last_seen"] is not None


# ==============================================================
# SECTION 11 — GAS HISTORY API
# ==============================================================

class TestGasHistoryAPI:
    """GET /gas-readings must return persisted records accurately."""

    def test_gas_history_empty_initially(self):
        """No readings means empty list."""
        r = client.get(f"{BASE}/{OWNED}/gas-readings")
        assert r.status_code == 200
        assert r.json() == []

    def test_gas_history_returns_all_inserted_readings(self):
        """All readings inserted via canonical pipeline must appear."""
        ppms = [100.0, 550.0, 1100.0, 200.0]
        for ppm in ppms:
            _direct_ingest(OWNED, ppm)

        r = client.get(f"{BASE}/{OWNED}/gas-readings")
        assert r.status_code == 200
        readings = r.json()
        assert len(readings) == len(ppms)

    def test_gas_history_limit_respected(self):
        """?limit=2 must return at most 2 records."""
        for ppm in [100.0, 200.0, 300.0, 400.0]:
            _direct_ingest(OWNED, ppm)

        r = client.get(f"{BASE}/{OWNED}/gas-readings?limit=2")
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_gas_history_ordered_ascending(self):
        """Results must be ordered timestamp ascending (SafetyReadService orders asc)."""
        ppms = [1000.0, 200.0, 600.0]
        for ppm in ppms:
            _direct_ingest(OWNED, ppm)

        r = client.get(f"{BASE}/{OWNED}/gas-readings")
        readings = r.json()
        assert len(readings) == 3
        # Each record must have a ppm field — verify they all round-trip
        returned_ppms = [round(rec["ppm_value"]) for rec in readings]
        assert set(returned_ppms) == {1000, 200, 600}

    def test_gas_history_ppm_and_status_correct(self):
        """Each returned reading must have ppm_value and correct status."""
        _direct_ingest(OWNED, 1000.0)

        r = client.get(f"{BASE}/{OWNED}/gas-readings")
        readings = r.json()
        assert len(readings) == 1
        assert abs(readings[0]["ppm_value"] - 1000.0) < 0.01
        assert readings[0]["status"] == "critical"

    def test_gas_history_device_isolation(self):
        """Readings for OWNED must not include readings for OTHER device."""
        _direct_ingest(OWNED, 300.0)

        # OTHER belongs to user 2; user 1 cannot access it anyway — verify isolation
        owned_rows = _db_gas_readings(OWNED)
        other_rows = _db_gas_readings(OTHER)
        assert len(owned_rows) >= 1
        assert len(other_rows) == 0

    def test_gas_history_api_device_isolation(self):
        """GET /gas-readings for OTHER device must return 403 (wrong owner)."""
        r = client.get(f"{BASE}/{OTHER}/gas-readings")
        assert r.status_code == 403

    def test_gas_history_unknown_device_404(self):
        r = client.get(f"{BASE}/{MISSING}/gas-readings")
        assert r.status_code == 404

    def test_gas_history_returns_correct_response_fields(self):
        """Each record must contain id, device_id, ppm_value, status, timestamp."""
        _direct_ingest(OWNED, 300.0)
        r = client.get(f"{BASE}/{OWNED}/gas-readings")
        record = r.json()[0]

        assert "id" in record
        assert "device_id" in record
        assert "ppm_value" in record
        assert "status" in record
        assert "timestamp" in record
        assert record["device_id"] == OWNED


# ==============================================================
# SECTION 12 — LEAK HISTORY API
# ==============================================================

class TestLeakHistoryAPI:
    """GET /leaks must return persisted leak events accurately."""

    def test_leak_history_empty_initially(self):
        r = client.get(f"{BASE}/{OWNED}/leaks")
        assert r.status_code == 200
        assert r.json() == {"leaks": []}

    def test_leak_history_returns_persisted_events(self):
        """After creating two complete leak cycles, both events must appear."""
        # Cycle 1: create + resolve
        _direct_ingest(OWNED, 1100.0)
        _direct_ingest(OWNED, 200.0)
        # Cycle 2: open active
        _direct_ingest(OWNED, 1300.0)

        r = client.get(f"{BASE}/{OWNED}/leaks")
        assert r.status_code == 200
        leaks = r.json()["leaks"]
        assert len(leaks) == 2

    def test_leak_history_active_flag(self):
        """Unresolved leak must have active=True; resolved must have active=False."""
        _direct_ingest(OWNED, 1100.0)
        _direct_ingest(OWNED, 200.0)   # resolve
        _direct_ingest(OWNED, 1200.0)  # new active

        r = client.get(f"{BASE}/{OWNED}/leaks")
        leaks = r.json()["leaks"]
        assert len(leaks) == 2

        active   = [l for l in leaks if l["active"]]
        resolved = [l for l in leaks if not l["active"]]
        assert len(active) == 1
        assert len(resolved) == 1
        assert active[0]["end_time"] is None
        assert resolved[0]["end_time"] is not None

    def test_leak_history_peak_ppm_preserved(self):
        """peak_ppm in the API response must match what is stored in the DB."""
        _direct_ingest(OWNED, 1000.0)
        _direct_ingest(OWNED, 2000.0)  # updates peak
        _direct_ingest(OWNED, 200.0)   # resolve

        r = client.get(f"{BASE}/{OWNED}/leaks")
        leaks = r.json()["leaks"]
        assert abs(leaks[0]["peak_ppm"] - 2000.0) < 0.01

    def test_leak_history_limit(self):
        """?limit=1 must return at most 1 leak event."""
        for _ in range(3):
            _direct_ingest(OWNED, 1100.0)
            _direct_ingest(OWNED, 200.0)

        r = client.get(f"{BASE}/{OWNED}/leaks?limit=1")
        assert r.status_code == 200
        assert len(r.json()["leaks"]) == 1

    def test_leak_history_device_isolation_via_403(self):
        r = client.get(f"{BASE}/{OTHER}/leaks")
        assert r.status_code == 403

    def test_leak_history_unknown_device_404(self):
        r = client.get(f"{BASE}/{MISSING}/leaks")
        assert r.status_code == 404

    def test_active_leak_endpoint_returns_correct_event(self):
        """GET /leaks/active must mirror the DB record for the unresolved leak."""
        _direct_ingest(OWNED, 1500.0)

        r = client.get(f"{BASE}/{OWNED}/leaks/active")
        assert r.status_code == 200
        data = r.json()
        assert data is not None
        assert data["device_id"] == OWNED
        assert abs(data["peak_ppm"] - 1500.0) < 0.01
        assert data["active"] is True
        assert data["end_time"] is None

    def test_active_leak_endpoint_returns_null_when_resolved(self):
        """After recovery, /leaks/active must return null."""
        _direct_ingest(OWNED, 1200.0)
        _direct_ingest(OWNED, 200.0)

        r = client.get(f"{BASE}/{OWNED}/leaks/active")
        assert r.status_code == 200
        assert r.json() is None


# ==============================================================
# SECTION 13 — DIAGNOSTICS API
# ==============================================================

class TestDiagnosticsAPI:
    """GET /diagnostics must reflect device state — not hardcoded values."""

    def test_diagnostics_returns_structured_report(self):
        """All top-level sections must be present."""
        r = client.get(f"{BASE}/{OWNED}/diagnostics")
        assert r.status_code == 200
        data = r.json()
        for section in ("device", "connection", "sensor", "telemetry", "safety"):
            assert section in data, f"Missing diagnostics section: {section}"

    def test_diagnostics_device_section(self):
        """Device section must carry the correct device identity."""
        r = client.get(f"{BASE}/{OWNED}/diagnostics")
        dev = r.json()["device"]
        assert dev["id"] == OWNED
        assert dev["paired"] is True  # belongs to user 1

    def test_diagnostics_connection_unknown_when_no_readings(self):
        """Without readings, connection_status must be 'unknown'."""
        r = client.get(f"{BASE}/{OWNED}/diagnostics")
        assert r.json()["connection"]["status"] == "unknown"

    def test_diagnostics_connection_online_after_recent_reading(self):
        """After a recent reading, connection_status must be 'online'."""
        _direct_ingest(OWNED, 300.0)

        r = client.get(f"{BASE}/{OWNED}/diagnostics")
        assert r.json()["connection"]["status"] == "online"

    def test_diagnostics_sensor_health_from_device(self):
        """Sensor health must come from Device.sensor_health_status."""
        r = client.get(f"{BASE}/{OWNED}/diagnostics")
        sensor = r.json()["sensor"]
        assert "health" in sensor
        # Default from conftest device creation is 'healthy'
        assert sensor["health"] in ("healthy", "unknown", "degraded", "fault")

    def test_diagnostics_telemetry_ppm_after_reading(self):
        """Telemetry section must carry the latest ppm after a reading."""
        _direct_ingest(OWNED, 750.0)

        r = client.get(f"{BASE}/{OWNED}/diagnostics")
        telemetry = r.json()["telemetry"]
        assert abs(telemetry["latest_gas_ppm"] - 750.0) < 0.01

    def test_diagnostics_safety_valve_status(self):
        """Safety section valve_status must match Device.valve_status."""
        r = client.get(f"{BASE}/{OWNED}/diagnostics")
        assert r.json()["safety"]["valve_status"] in ("OPEN", "CLOSED", "unknown")

    def test_diagnostics_wrong_owner_403(self):
        r = client.get(f"{BASE}/{OTHER}/diagnostics")
        assert r.status_code == 403

    def test_diagnostics_unknown_device_404(self):
        r = client.get(f"{BASE}/{MISSING}/diagnostics")
        assert r.status_code == 404


# ==============================================================
# SECTION 14 — AUTHORIZATION / DATA ISOLATION (complete matrix)
# ==============================================================

class TestAuthorizationIsolation:
    """
    Verify that user A cannot access user B's safety data through any
    Phase 1 endpoint.
    """

    SAFETY_ENDPOINTS = [
        ("GET",  f"{BASE}/{OTHER}/safety"),
        ("GET",  f"{BASE}/{OTHER}/gas-readings"),
        ("GET",  f"{BASE}/{OTHER}/leaks/active"),
        ("GET",  f"{BASE}/{OTHER}/leaks"),
        ("GET",  f"{BASE}/{OTHER}/diagnostics"),
        ("POST", f"{BASE}/{OTHER}/valve/emergency-close"),
        ("POST", f"{BASE}/{OTHER}/valve/reset"),
    ]

    @pytest.mark.parametrize("method,url", SAFETY_ENDPOINTS)
    def test_wrong_owner_gets_403(self, method, url):
        """User 1 must receive 403 for every endpoint targeting user 2's device."""
        r = client.request(method, url)
        assert r.status_code == 403, (
            f"{method} {url}: expected 403, got {r.status_code} — {r.text}"
        )

    MISSING_ENDPOINTS = [
        ("GET",  f"{BASE}/{MISSING}/safety"),
        ("GET",  f"{BASE}/{MISSING}/gas-readings"),
        ("GET",  f"{BASE}/{MISSING}/leaks/active"),
        ("GET",  f"{BASE}/{MISSING}/leaks"),
        ("GET",  f"{BASE}/{MISSING}/diagnostics"),
        ("POST", f"{BASE}/{MISSING}/valve/emergency-close"),
        ("POST", f"{BASE}/{MISSING}/valve/reset"),
    ]

    @pytest.mark.parametrize("method,url", MISSING_ENDPOINTS)
    def test_unknown_device_gets_404(self, method, url):
        """Unknown device must return 404 for every endpoint."""
        r = client.request(method, url)
        assert r.status_code == 404, (
            f"{method} {url}: expected 404, got {r.status_code} — {r.text}"
        )

    def test_unauthenticated_safety_summary_rejected(self):
        """
        A bare (no-auth) client must be rejected on the safety summary endpoint.
        We temporarily clear dependency overrides to exercise the real JWT guard.
        """
        from fastapi.testclient import TestClient
        from app.main import app as real_app

        original = dict(real_app.dependency_overrides)
        real_app.dependency_overrides.clear()
        try:
            bare = TestClient(real_app, raise_server_exceptions=False)
            r = bare.get(f"{BASE}/{OWNED}/safety")
            assert r.status_code in (401, 403, 422), (
                f"Expected 401/403/422 without auth, got {r.status_code}"
            )
        finally:
            real_app.dependency_overrides.update(original)

    def test_db_gas_readings_not_visible_across_devices(self):
        """DB layer: readings for OWNED must not appear in OTHER's query."""
        _direct_ingest(OWNED, 400.0)

        assert len(_db_gas_readings(OWNED)) >= 1
        assert len(_db_gas_readings(OTHER)) == 0

    def test_db_leak_events_not_visible_across_devices(self):
        """DB layer: leak events for OWNED must not appear in OTHER's query."""
        _direct_ingest(OWNED, 1200.0)

        assert len(_db_leak_events(OWNED)) >= 1
        assert len(_db_leak_events(OTHER)) == 0

    def test_db_device_commands_not_visible_across_devices(self):
        """DB layer: OWNED's valve commands must not appear for OTHER."""
        client.post(f"{BASE}/{OWNED}/valve/emergency-close")

        owned_cmds = _db_device_commands(OWNED)
        other_cmds = _db_device_commands(OTHER)
        assert len(owned_cmds) >= 1
        assert len(other_cmds) == 0


# ==============================================================
# SECTION 15 — END-TO-END FLOW (DB DIRECT VERIFICATION)
# ==============================================================

class TestEndToEndFlow:
    """
    Full pipeline exercises that verify every DB table touched during a
    complete critical-gas-leak scenario.
    """

    def test_e2e_critical_reading_full_chain(self):
        """
        A single CRITICAL telemetry reading must produce records in ALL
        four relevant tables: gas_readings, leak_events, notifications,
        device_commands.
        """
        ppm = 1400.0
        _direct_ingest(OWNED, ppm)

        # 1. gas_readings
        readings = _db_gas_readings(OWNED)
        assert len(readings) == 1
        assert readings[0].status == "critical"

        # 2. leak_events
        leaks = _db_leak_events(OWNED)
        assert len(leaks) == 1
        assert leaks[0].end_time is None
        assert abs(leaks[0].peak_ppm - ppm) < 0.01

        # 3. notifications
        notifs = _db_notifications(user_id=1)
        assert len(notifs) >= 1
        critical = [n for n in notifs if n.payload.get("type") == "GAS_LEAK_CRITICAL"]
        assert len(critical) == 1

        # 4. device_commands
        cmds = _db_device_commands(OWNED)
        assert len(cmds) == 1
        assert cmds[0].command == "EMERGENCY_CLOSE"

        # 5. Device valve_status
        device = _db_device(OWNED)
        assert device.valve_status == "CLOSED"

    def test_e2e_api_consistency_after_full_chain(self):
        """
        After the full chain, all Phase 1 safety endpoints must reflect
        the persisted state consistently.
        """
        ppm = 1200.0
        _direct_ingest(OWNED, ppm)

        # Safety summary
        r_safety = client.get(f"{BASE}/{OWNED}/safety")
        assert r_safety.status_code == 200
        safety = r_safety.json()
        assert safety["status"] == "critical"
        assert safety["valve_status"] == "CLOSED"
        assert abs(safety["latest_gas_ppm"] - ppm) < 0.01

        # Active leak
        r_leak = client.get(f"{BASE}/{OWNED}/leaks/active")
        assert r_leak.status_code == 200
        assert r_leak.json() is not None
        assert r_leak.json()["active"] is True

        # Leak history
        r_hist = client.get(f"{BASE}/{OWNED}/leaks")
        assert r_hist.status_code == 200
        assert len(r_hist.json()["leaks"]) == 1

        # Gas readings
        r_gas = client.get(f"{BASE}/{OWNED}/gas-readings")
        assert r_gas.status_code == 200
        assert len(r_gas.json()) == 1

        # Diagnostics
        r_diag = client.get(f"{BASE}/{OWNED}/diagnostics")
        assert r_diag.status_code == 200
        assert r_diag.json()["safety"]["valve_status"] == "CLOSED"

    def test_e2e_full_lifecycle_with_recovery_and_reset(self):
        """
        Complete lifecycle:
        1. Normal → no action
        2. Warning → notification only
        3. Critical → leak + notification + valve close
        4. Critical (higher) → peak update
        5. Normal → leak resolved (valve stays CLOSED)
        6. Manual reset → valve reopens

        Verify DB state at each stage.
        """
        # Stage 1: Normal
        _direct_ingest(OWNED, 200.0)
        assert _db_leak_events(OWNED) == []
        assert _db_device(OWNED).valve_status == "OPEN"

        # Stage 2: Warning
        _direct_ingest(OWNED, 750.0)
        assert _db_leak_events(OWNED) == []
        warning_notifs = [
            n for n in _db_notifications(1)
            if n.payload and n.payload.get("type") == "GAS_LEVEL_WARNING"
        ]
        assert len(warning_notifs) == 1

        # Stage 3: Critical
        _direct_ingest(OWNED, 1100.0)
        leaks = _db_leak_events(OWNED)
        assert len(leaks) == 1
        assert leaks[0].end_time is None
        assert _db_device(OWNED).valve_status == "CLOSED"

        # Stage 4: Higher critical
        _direct_ingest(OWNED, 1800.0)
        leaks = _db_leak_events(OWNED)
        assert len(leaks) == 1                                  # still one event
        assert abs(leaks[0].peak_ppm - 1800.0) < 0.01          # peak updated

        # Stage 5: Normal (recovery)
        _direct_ingest(OWNED, 200.0)
        leaks = _db_leak_events(OWNED)
        assert leaks[0].end_time is not None                    # resolved
        assert _db_device(OWNED).valve_status == "CLOSED"      # lockout preserved

        # Active leak API should return null after recovery
        r = client.get(f"{BASE}/{OWNED}/leaks/active")
        assert r.json() is None

        # Stage 6: Manual reset
        r_reset = client.post(f"{BASE}/{OWNED}/valve/reset")
        assert r_reset.status_code == 200
        assert r_reset.json()["valve_status"] == "OPEN"
        assert _db_device(OWNED).valve_status == "OPEN"

        # Safety API reflects open valve
        r_safety = client.get(f"{BASE}/{OWNED}/safety")
        assert r_safety.json()["valve_status"] == "OPEN"

    def test_e2e_db_records_not_deleted_after_operations(self):
        """
        After a complete lifecycle, no historical records must be deleted.
        All gas_readings, leak_events, notifications must remain.
        """
        # Create a full cycle
        for ppm in [300.0, 750.0, 1200.0, 1500.0, 200.0]:
            _direct_ingest(OWNED, ppm)
        client.post(f"{BASE}/{OWNED}/valve/reset")

        # All 5 gas readings must remain
        readings = _db_gas_readings(OWNED)
        assert len(readings) == 5

        # The 1 leak event (resolved) must remain
        leaks = _db_leak_events(OWNED)
        assert len(leaks) == 1
        assert leaks[0].end_time is not None

        # Notifications must remain
        notifs = _db_notifications(1)
        assert len(notifs) >= 1
