import math
import logging
import httpx
from fastapi import HTTPException, status
from app.core.config import settings
from app.schemas.gas_agency import GasAgency, GasAgenciesResponse, UserLocation

logger = logging.getLogger(__name__)

PLACES_API_BASE = "https://places.googleapis.com/v1"
FIELD_MASK = (
    "places.id,places.displayName,places.formattedAddress,places.location,"
    "places.nationalPhoneNumber,places.internationalPhoneNumber,places.googleMapsUri,"
    "places.rating,places.userRatingCount"
)


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in kilometers."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)


class GasAgencyService:
    @staticmethod
    def _parse_place(place: dict, user_lat: float, user_lng: float) -> GasAgency | None:
        """Parse raw Google Places API (New) object into GasAgency schema."""
        place_id = place.get("id")
        if not place_id:
            return None

        display_name = place.get("displayName", {}).get("text") or "LPG Gas Agency"
        formatted_address = place.get("formattedAddress") or "Address not provided"
        location = place.get("location") or {}
        agency_lat = location.get("latitude")
        agency_lng = location.get("longitude")

        if agency_lat is None or agency_lng is None:
            return None

        distance_km = haversine_distance_km(user_lat, user_lng, agency_lat, agency_lng)
        phone = place.get("nationalPhoneNumber") or place.get("internationalPhoneNumber")

        maps_uri = place.get("googleMapsUri") or (
            f"https://www.google.com/maps/search/?api=1&query={agency_lat},{agency_lng}&query_place_id={place_id}"
        )

        return GasAgency(
            id=place_id,
            name=display_name,
            address=formatted_address,
            latitude=agency_lat,
            longitude=agency_lng,
            distance_km=distance_km,
            phone_number=phone,
            google_maps_url=maps_uri,
            rating=place.get("rating"),
            user_ratings_total=place.get("userRatingCount"),
        )

    async def get_nearby_agencies(
        self,
        latitude: float,
        longitude: float,
        radius: int = 10000,
        query: str | None = None,
    ) -> GasAgenciesResponse:
        """
        Search for LPG gas agencies and gas distributors using Google Places API (New).
        Searches via textQuery with locationBias/locationRestriction and nearby gas distributors,
        sorts results by distance from the user.
        """
        api_key = settings.places_api_key
        if not api_key:
            logger.warning("[GasAgencyService] GOOGLE_PLACES_API_KEY is not configured.")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Google Places API key is not configured on the backend. "
                    "Please set GOOGLE_PLACES_API_KEY in your Render dashboard."
                ),
            )

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": FIELD_MASK,
        }

        # Text search tailored to LPG gas agencies & distributors
        text_query = query.strip() if query and query.strip() else "LPG gas agency distributor"

        search_payload = {
            "textQuery": text_query,
            "locationBias": {
                "circle": {
                    "center": {
                        "latitude": latitude,
                        "longitude": longitude,
                    },
                    "radius": float(radius),
                }
            },
            "maxResultCount": 20,
        }

        nearby_payload = {
            "includedTypes": ["gas_station"],
            "maxResultCount": 10,
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": latitude,
                        "longitude": longitude,
                    },
                    "radius": float(radius),
                }
            },
        }

        collected_places: dict[str, dict] = {}

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                # 1. Primary: Text Search with LPG keywords & location bias
                resp_text = await client.post(
                    f"{PLACES_API_BASE}/places:searchText",
                    json=search_payload,
                    headers=headers,
                )

                if resp_text.status_code == 200:
                    data = resp_text.json()
                    for p in data.get("places", []):
                        pid = p.get("id")
                        if pid:
                            collected_places[pid] = p
                elif resp_text.status_code in (400, 401, 403):
                    error_json = resp_text.json() if resp_text.content else {}
                    err_msg = error_json.get("error", {}).get("message", resp_text.text)
                    logger.error(f"[GasAgencyService] Places API Error ({resp_text.status_code}): {err_msg}")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Google Places API error ({resp_text.status_code}): {err_msg}",
                    )

                # 2. Secondary: If text search returned fewer than 5 results and no custom query was provided,
                # also query searchNearby with gas_station to find any additional nearby gas distribution points
                if len(collected_places) < 5 and not query:
                    try:
                        resp_nearby = await client.post(
                            f"{PLACES_API_BASE}/places:searchNearby",
                            json=nearby_payload,
                            headers=headers,
                        )
                        if resp_nearby.status_code == 200:
                            data_nearby = resp_nearby.json()
                            for p in data_nearby.get("places", []):
                                pid = p.get("id")
                                if pid and pid not in collected_places:
                                    collected_places[pid] = p
                    except Exception as err:
                        logger.warning(f"[GasAgencyService] Optional searchNearby query omitted: {err}")

            except httpx.TimeoutException:
                logger.error("[GasAgencyService] Request to Google Places API timed out.")
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail="Google Places API connection timed out. Please try again.",
                )
            except HTTPException:
                raise
            except Exception as exc:
                logger.error(f"[GasAgencyService] Unexpected network error: {exc}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Failed to communicate with Google Places API: {str(exc)}",
                )

        # Parse and sort agencies by distance
        agencies: list[GasAgency] = []
        for raw_place in collected_places.values():
            parsed = self._parse_place(raw_place, user_lat=latitude, user_lng=longitude)
            if parsed and parsed.distance_km <= (radius / 1000.0) * 1.5:  # within search boundary
                agencies.append(parsed)

        # Sort strictly by ascending distance from the user
        agencies.sort(key=lambda a: a.distance_km)

        return GasAgenciesResponse(
            success=True,
            count=len(agencies),
            radius_meters=radius,
            user_location=UserLocation(latitude=latitude, longitude=longitude),
            agencies=agencies,
            message=None if agencies else f"No LPG gas agencies found within {radius // 1000} km of your location.",
        )


gas_agency_service = GasAgencyService()
