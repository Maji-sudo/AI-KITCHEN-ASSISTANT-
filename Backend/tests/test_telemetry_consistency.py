"""
Test Telemetry Consistency & Single Source of Truth
===================================================

Verifies:
1. Shared source of truth between /devices/{id}/safety and /telemetry/gas/{id}.
2. Historical gas readings endpoint (/devices/{id}/gas-readings) returns the
   most recent `limit` readings sorted chronologically ascending.
3. Ingesting critical 1100 PPM reading is reflected consistently in current
   safety state and historical time-series.
4. Simulation scenarios and manual data entry source tagging (SIMULATOR / MANUAL / IOT).
5. Canonical safety thresholds: normal < 500, warning 500–999, critical >= 1000.
"""

import pytest
from datetime import datetime, timezone, timedelta

from app.models.gas_reading import GasReading
from app.models.device import Device
from app.services.safety_classification import classify_gas
from app.services.simulation_service import simulation_service
from tests.conftest import client, TestingSessionLocal

OWNED_DEVICE = "paired_dev_1"
BASE = "/api/v1/devices"


def test_threshold_consistency_across_layers():
    """Verify project-wide canonical thresholds: normal < 500 | warning 500–999 | critical >= 1000."""
    assert classify_gas(0.0) == "normal"
    assert classify_gas(180.1) == "normal"
    assert classify_gas(499.9) == "normal"
    assert classify_gas(500.0) == "warning"
    assert classify_gas(750.0) == "warning"
    assert classify_gas(999.9) == "warning"
    assert classify_gas(1000.0) == "critical"
    assert classify_gas(1100.0) == "critical"
    assert classify_gas(2500.0) == "critical"


def test_consistent_source_of_truth_across_endpoints():
    """Both /devices/{id}/safety and /telemetry/gas/{id} must show the identical latest PPM and status."""
    now = datetime.now(timezone.utc)
    ingest_res = client.post(
        "/api/v1/telemetry/gas",
        json={
            "device_id": OWNED_DEVICE,
            "ppm_value": 320.5,
            "timestamp": now.isoformat(),
        },
    )
    assert ingest_res.status_code == 201

    # 1. Check /devices/{id}/safety
    safety_res = client.get(f"{BASE}/{OWNED_DEVICE}/safety")
    assert safety_res.status_code == 200
    safety_data = safety_res.json()

    # 2. Check /telemetry/gas/{id}
    telemetry_res = client.get(f"/api/v1/telemetry/gas/{OWNED_DEVICE}?limit=5")
    assert telemetry_res.status_code == 200
    telemetry_data = telemetry_res.json()

    assert len(telemetry_data) > 0
    latest_telemetry = telemetry_data[0]

    # Verify identical values and device ID
    assert safety_data["device_id"] == OWNED_DEVICE
    assert latest_telemetry["device_id"] == OWNED_DEVICE
    assert safety_data["latest_gas_ppm"] == latest_telemetry["ppm_value"]
    assert safety_data["status"] == latest_telemetry["status"]


def test_gas_history_returns_most_recent_records_in_ascending_order():
    """
    GET /devices/{id}/gas-readings?limit=N must return the MOST RECENT N records
    ordered in ASCENDING order (oldest to newest) for accurate live graphing.
    """
    now = datetime.now(timezone.utc)
    db = TestingSessionLocal()
    # Clean previous readings for test clarity
    db.query(GasReading).filter(GasReading.device_id == OWNED_DEVICE).delete()
    db.commit()

    # Seed 10 sequential readings spaced 1 minute apart
    ppms = [120.0, 130.0, 140.0, 150.0, 160.0, 170.0, 180.0, 520.0, 850.0, 1100.0]
    for i, ppm in enumerate(ppms):
        reading_time = now - timedelta(minutes=(len(ppms) - i))
        db.add(GasReading(
            device_id=OWNED_DEVICE,
            ppm_value=ppm,
            status=classify_gas(ppm),
            timestamp=reading_time,
            source="IOT",
        ))
    db.commit()
    db.close()

    # Request the last 4 readings
    res = client.get(f"{BASE}/{OWNED_DEVICE}/gas-readings?limit=4")
    assert res.status_code == 200
    readings = res.json()

    assert len(readings) == 4
    # Must be the last 4 values: [180.0, 520.0, 850.0, 1100.0]
    returned_ppms = [r["ppm_value"] for r in readings]
    assert returned_ppms == [180.0, 520.0, 850.0, 1100.0]

    # Chronologically ascending
    for j in range(len(readings) - 1):
        t1 = datetime.fromisoformat(readings[j]["timestamp"])
        t2 = datetime.fromisoformat(readings[j + 1]["timestamp"])
        assert t1 <= t2


def test_critical_1100_ppm_reflected_in_both_safety_and_history_series():
    """
    When an 1100 PPM critical reading is ingested, it must appear in /devices/{id}/safety
    AND as the latest point in /devices/{id}/gas-readings.
    """
    now = datetime.now(timezone.utc)
    res_ingest = client.post(
        "/api/v1/telemetry/gas",
        json={
            "device_id": OWNED_DEVICE,
            "ppm_value": 1100.0,
            "timestamp": now.isoformat(),
        },
    )
    assert res_ingest.status_code == 201

    # Safety status must report 1100.0 and critical
    res_safety = client.get(f"{BASE}/{OWNED_DEVICE}/safety")
    assert res_safety.status_code == 200
    safety_data = res_safety.json()
    assert safety_data["latest_gas_ppm"] == 1100.0
    assert safety_data["status"] == "critical"

    # Gas history must include 1100.0 as its most recent point
    res_history = client.get(f"{BASE}/{OWNED_DEVICE}/gas-readings?limit=30")
    assert res_history.status_code == 200
    history_data = res_history.json()
    assert len(history_data) > 0
    assert history_data[-1]["ppm_value"] == 1100.0
    assert history_data[-1]["status"] == "critical"


def test_simulation_scenarios_and_source_tagging():
    """
    Verify simulation scenarios set proper thresholds and tag records as SIMULATOR:
    - normal: PPM < 500, status "normal"
    - warning: 500 <= PPM < 1000, status "warning"
    - critical: PPM >= 1000, status "critical"
    """
    db = TestingSessionLocal()
    try:
        # 1. Normal scenario
        normal_res = simulation_service.generate_safety_scenario(db, OWNED_DEVICE, user_id=1, scenario="normal")
        assert normal_res["latest_status"] == "normal"
        assert normal_res["latest_ppm"] < 500.0

        # 2. Warning scenario
        warn_res = simulation_service.generate_safety_scenario(db, OWNED_DEVICE, user_id=1, scenario="warning")
        assert warn_res["latest_status"] == "warning"
        assert 500.0 <= warn_res["latest_ppm"] < 1000.0

        # 3. Critical scenario
        crit_res = simulation_service.generate_safety_scenario(db, OWNED_DEVICE, user_id=1, scenario="critical")
        assert crit_res["latest_status"] == "critical"
        assert crit_res["latest_ppm"] >= 1000.0

        # Verify source tagging via read API
        readings_res = client.get(f"{BASE}/{OWNED_DEVICE}/gas-readings?limit=10")
        assert readings_res.status_code == 200
        readings = readings_res.json()
        assert any(r.get("source") == "SIMULATOR" for r in readings)
    finally:
        db.close()


def test_manual_entry_source_tagging():
    """Manual telemetry entries are tagged with source='MANUAL'."""
    now = datetime.now(timezone.utc)
    res = client.post(
        "/api/v1/telemetry/manual/gas",
        json={
            "device_id": OWNED_DEVICE,
            "ppm_value": 650.0,
            "timestamp": now.isoformat(),
        },
    )
    assert res.status_code == 201
    entry = res.json()
    assert entry["source"] == "MANUAL"
    assert entry["ppm_value"] == 650.0
    assert entry["status"] == "warning"

    # Current safety state should reflect the manual reading
    safety_res = client.get(f"{BASE}/{OWNED_DEVICE}/safety")
    assert safety_res.status_code == 200
    assert safety_res.json()["source"] == "MANUAL"
