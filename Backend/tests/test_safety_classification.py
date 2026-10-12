# tests/test_safety_classification.py
"""
Phase 2 — Safety Classification Engine
Tests the authoritative classify_gas thresholds across all three telemetry sources.

Shared fixtures (engine, client, setup_db) live in conftest.py.
"""
import pytest
from tests.conftest import client          # shared TestClient

# ------------------------------------------------------------
# Classification boundary tests – all sources should behave the same
# ------------------------------------------------------------
@pytest.mark.parametrize(
    "ppm,expected_status",
    [
        (0,    "normal"),
        (1,    "normal"),
        (499,  "normal"),
        (500,  "warning"),
        (501,  "warning"),
        (999,  "warning"),
        (1000, "critical"),
        (1001, "critical"),
        (5000, "critical"),
    ],
)
def test_classification_boundaries(ppm, expected_status):
    for source in ["MANUAL", "SIMULATOR", "IOT"]:
        payload = {"device_id": "dev123", "ppm_value": ppm, "source": source}
        response = client.post("/api/v1/telemetry/gas", json=payload)
        assert response.status_code == 201, (
            f"source={source} ppm={ppm}: expected 201, got {response.status_code} — {response.text}"
        )
        data = response.json()
        assert data["status"] == expected_status, (
            f"source={source} ppm={ppm}: expected status={expected_status!r}, got {data['status']!r}"
        )


# ------------------------------------------------------------
# Invalid / edge value tests
# ------------------------------------------------------------
def test_negative_ppm_accepted_as_normal():
    """Negative PPM passes schema (no lower-bound validation) and classifies as normal."""
    payload = {"device_id": "dev123", "ppm_value": -10, "source": "IOT"}
    response = client.post("/api/v1/telemetry/gas", json=payload)
    assert response.status_code == 201
    assert response.json()["status"] == "normal"


def test_missing_ppm_rejected():
    payload = {"device_id": "dev123", "source": "IOT"}
    response = client.post("/api/v1/telemetry/gas", json=payload)
    assert response.status_code == 422


def test_invalid_type_ppm_rejected():
    payload = {"device_id": "dev123", "ppm_value": "not-a-number", "source": "IOT"}
    response = client.post("/api/v1/telemetry/gas", json=payload)
    assert response.status_code == 422
