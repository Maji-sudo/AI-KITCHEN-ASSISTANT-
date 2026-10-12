import pytest
from fastapi import status
from tests.conftest import client

def test_manual_telemetry_success():
    response = client.post(
        "/api/v1/telemetry/manual/gas",
        json={"device_id": "paired_dev_1", "ppm_value": 600, "source": "MANUAL"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["device_id"] == "paired_dev_1"
    assert data["ppm_value"] == 600
    assert data["source"] == "MANUAL"

def test_manual_telemetry_wrong_user():
    response = client.post(
        "/api/v1/telemetry/manual/gas",
        json={"device_id": "paired_dev_2", "ppm_value": 400},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_manual_telemetry_invalid_payload():
    response = client.post(
        "/api/v1/telemetry/manual/gas",
        json={"device_id": "paired_dev_1"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
