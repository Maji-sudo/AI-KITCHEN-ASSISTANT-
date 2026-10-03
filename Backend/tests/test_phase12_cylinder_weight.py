import pytest
from fastapi import status
from datetime import datetime, timezone
from tests.conftest import client

def test_cylinder_provisioning_success():
    response = client.post(
        "/api/v1/devices/paired_dev_1/cylinders",
        json={
            "tare_weight_g": 15300,
            "full_weight_g": 29500,
            "cylinder_type": "14.2kg",
            "device_id": "paired_dev_1"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["device_id"] == "paired_dev_1"
    assert data["tare_weight_g"] == 15300
    assert data["full_weight_g"] == 29500

def test_cylinder_provisioning_unauthorized():
    response = client.post(
        "/api/v1/devices/paired_dev_2/cylinders",
        json={
            "tare_weight_g": 15300,
            "full_weight_g": 29500,
            "device_id": "paired_dev_2"
        }
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_weight_telemetry_iot_success():
    response = client.post(
        "/api/v1/telemetry/weight",
        json={
            "device_id": "paired_dev_1",
            "weight_g": 29000,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    
    # Retrieve it
    get_resp = client.get("/api/v1/telemetry/weight/paired_dev_1")
    assert get_resp.status_code == status.HTTP_200_OK
    assert len(get_resp.json()) == 1
    assert get_resp.json()[0]["weight_g"] == 29000

def test_weight_telemetry_manual_unauthorized():
    response = client.post(
        "/api/v1/telemetry/manual/weight",
        json={
            "device_id": "paired_dev_2",
            "weight_g": 25000,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_refill_prediction_unauthorized():
    response = client.get("/api/v1/refill/paired_dev_2")
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_booking_creation_and_retrieval():
    # Create booking without sending user_id
    post_resp = client.post(
        "/api/v1/bookings/",
        json={
            "device_id": "paired_dev_1",
            "distributor": "HP Gas",
            "booking_date": datetime.now(timezone.utc).isoformat(),
            "source": "app"
        }
    )
    assert post_resp.status_code == status.HTTP_201_CREATED
    booking_data = post_resp.json()
    assert booking_data["user_id"] == 1  # Should be automatically assigned by JWT mock
    assert booking_data["status"] == "pending"
    assert booking_data["distributor"] == "HP Gas"
    booking_id = booking_data["id"]

    # Retrieve bookings
    get_resp = client.get("/api/v1/bookings/")
    assert get_resp.status_code == status.HTTP_200_OK
    assert len(get_resp.json()) == 1
    assert get_resp.json()[0]["id"] == booking_id

def test_integration_lifecycle_e2e():
    # 1. Provision Cylinder
    client.post(
        "/api/v1/devices/paired_dev_1/cylinders",
        json={"tare_weight_g": 15300, "full_weight_g": 29500, "device_id": "paired_dev_1"}
    )
    
    # 2. Ingest weight telemetry (representing consumption over time)
    client.post(
        "/api/v1/telemetry/weight",
        json={"device_id": "paired_dev_1", "weight_g": 20000, "timestamp": datetime.now(timezone.utc).isoformat()}
    )
    
    # 3. Get Refill Prediction (this will trigger `compute_refill_prediction`)
    predict_resp = client.post("/api/v1/refill/paired_dev_1/predict")
    assert predict_resp.status_code == status.HTTP_200_OK
    pred_data = predict_resp.json()
    assert "days_left" in pred_data
    assert "predicted_empty_date" in pred_data
    assert "confidence" in pred_data
    # Current net gas = 20000 - 15300 = 4700g. 
    # Default avg_daily_burn = 350g -> 4700 / 350 = 13.4 -> 13 days
    assert pred_data["days_left"] == 13
    
    # 4. Make a booking
    booking_resp = client.post(
        "/api/v1/bookings/",
        json={
            "device_id": "paired_dev_1",
            "distributor": "Bharatgas",
            "booking_date": datetime.now(timezone.utc).isoformat()
        }
    )
    assert booking_resp.status_code == status.HTTP_201_CREATED
    b_id = booking_resp.json()["id"]
    
    # 5. Update booking status
    patch_resp = client.patch(f"/api/v1/bookings/{b_id}/status?status=confirmed")
    assert patch_resp.status_code == status.HTTP_200_OK
    assert patch_resp.json()["status"] == "confirmed"
