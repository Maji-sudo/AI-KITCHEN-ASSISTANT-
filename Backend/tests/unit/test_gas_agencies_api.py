import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.services.gas_agency_service import haversine_distance_km, gas_agency_service


def test_haversine_distance_calculation():
    """Verify haversine distance calculates accurate geographic distance."""
    # Bangalore City Center (12.9716, 77.5946) to Koramangala (12.9352, 77.6245) is ~5.2 km
    dist = haversine_distance_km(12.9716, 77.5946, 12.9352, 77.6245)
    assert 4.5 <= dist <= 6.0

    # Same location should be 0.0 km
    assert haversine_distance_km(12.9352, 77.6245, 12.9352, 77.6245) == 0.0


def test_invalid_coordinates_rejected():
    """Verify out-of-bounds coordinates return HTTP 422."""
    client = TestClient(app)

    # Latitude > 90
    resp = client.get("/api/v1/gas-agencies/nearby?latitude=95.0&longitude=77.0")
    assert resp.status_code == 422

    # Latitude < -90
    resp = client.get("/api/v1/gas-agencies/nearby?latitude=-95.0&longitude=77.0")
    assert resp.status_code == 422

    # Longitude > 180
    resp = client.get("/api/v1/gas-agencies/nearby?latitude=12.0&longitude=185.0")
    assert resp.status_code == 422

    # Radius out of range
    resp = client.get("/api/v1/gas-agencies/nearby?latitude=12.0&longitude=77.0&radius=100")
    assert resp.status_code == 422


def test_missing_api_key_returns_503(monkeypatch):
    """When GOOGLE_PLACES_API_KEY is not configured, endpoint returns 503."""
    monkeypatch.setattr("app.core.config.settings.GOOGLE_PLACES_API_KEY", "")
    monkeypatch.setattr("app.core.config.settings.GOOGLE_MAPS_API_KEY", "")

    client = TestClient(app)
    # Test both /api/v1 and /api endpoints
    for prefix in ["/api/v1", "/api"]:
        resp = client.get(f"{prefix}/gas-agencies/nearby?latitude=12.9352&longitude=77.6245")
        assert resp.status_code == 503
        data = resp.json()
        assert "Google Places API key is not configured" in data["detail"]


@pytest.mark.anyio
async def test_gas_agency_parsing_and_sorting(monkeypatch):
    """Verify Places API (New) response is parsed, distance computed, and sorted ascending."""
    monkeypatch.setattr("app.core.config.settings.GOOGLE_PLACES_API_KEY", "mock_key_12345")

    user_lat, user_lng = 12.9716, 77.5946

    # Mock Google Places API response
    # Agency 1 is ~5.2 km away
    # Agency 2 is ~1.5 km away
    mock_places_data = {
        "places": [
            {
                "id": "place_far_1",
                "displayName": {"text": "Koramangala HP Gas Agency", "languageCode": "en"},
                "formattedAddress": "80 Feet Rd, Koramangala, Bengaluru, Karnataka 560034",
                "location": {"latitude": 12.9352, "longitude": 77.6245},
                "nationalPhoneNumber": "080 2553 1111",
                "internationalPhoneNumber": "+91 80 2553 1111",
                "googleMapsUri": "https://maps.google.com/?cid=111",
                "rating": 4.3,
                "userRatingCount": 120,
            },
            {
                "id": "place_near_2",
                "displayName": {"text": "MG Road Indane Distributor", "languageCode": "en"},
                "formattedAddress": "MG Road, Bengaluru, Karnataka 560001",
                "location": {"latitude": 12.9750, "longitude": 77.6050},
                "nationalPhoneNumber": "080 2558 2222",
                "internationalPhoneNumber": "+91 80 2558 2222",
                "googleMapsUri": "https://maps.google.com/?cid=222",
                "rating": 4.6,
                "userRatingCount": 85,
            },
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_places_data

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        res = await gas_agency_service.get_nearby_agencies(
            latitude=user_lat,
            longitude=user_lng,
            radius=10000,
        )

    assert res.success is True
    assert res.count == 2
    # Verify sorted by distance (nearer first)
    assert res.agencies[0].id == "place_near_2"
    assert res.agencies[0].distance_km < res.agencies[1].distance_km
    assert res.agencies[0].phone_number == "080 2558 2222"
    assert res.agencies[1].id == "place_far_1"
    assert res.agencies[1].phone_number == "080 2553 1111"


def test_api_endpoint_with_mocked_service(monkeypatch):
    """Test full HTTP request/response through TestClient."""
    from app.schemas.gas_agency import GasAgenciesResponse, GasAgency, UserLocation

    mock_response = GasAgenciesResponse(
        success=True,
        count=1,
        radius_meters=10000,
        user_location=UserLocation(latitude=12.9352, longitude=77.6245),
        agencies=[
            GasAgency(
                id="place_test_abc",
                name="SafeGas Certified HP Distributor",
                address="12th Main, Bengaluru",
                latitude=12.9360,
                longitude=77.6250,
                distance_km=0.15,
                phone_number="+91 94936 02222",
                google_maps_url="https://maps.google.com/?cid=test",
                rating=4.5,
                user_ratings_total=50,
            )
        ],
    )

    with patch.object(gas_agency_service, "get_nearby_agencies", return_value=mock_response):
        client = TestClient(app)
        resp = client.get("/api/v1/gas-agencies/nearby?latitude=12.9352&longitude=77.6245")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["count"] == 1
        assert data["agencies"][0]["name"] == "SafeGas Certified HP Distributor"
        assert data["agencies"][0]["phone_number"] == "+91 94936 02222"
        assert data["agencies"][0]["distance_km"] == 0.15
