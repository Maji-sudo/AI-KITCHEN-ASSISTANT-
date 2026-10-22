from fastapi import APIRouter, Query, status
from app.schemas.gas_agency import GasAgenciesResponse
from app.services.gas_agency_service import gas_agency_service

router = APIRouter(
    prefix="/gas-agencies",
    tags=["gas-agencies"],
)


@router.get(
    "/nearby",
    response_model=GasAgenciesResponse,
    status_code=status.HTTP_200_OK,
    summary="Find nearby LPG gas agencies and distributors",
)
async def get_nearby_gas_agencies(
    latitude: float = Query(
        ...,
        ge=-90.0,
        le=90.0,
        description="User geographical latitude coordinate (-90 to 90)",
        examples=[12.9352],
    ),
    longitude: float = Query(
        ...,
        ge=-180.0,
        le=180.0,
        description="User geographical longitude coordinate (-180 to 180)",
        examples=[77.6245],
    ),
    radius: int = Query(
        default=10000,
        ge=500,
        le=50000,
        description="Search radius in meters (default 10,000m / 10km, min 500m, max 50,000m)",
    ),
    query: str | None = Query(
        default=None,
        description="Optional specific search text query (e.g. 'HP Gas', 'Indane', 'Bharat Gas')",
    ),
):
    """
    Search for verified LPG gas agencies and cylinder distributors near the specified GPS coordinates
    using the Google Places API (New). Results are sorted ascending by Haversine distance.
    """
    return await gas_agency_service.get_nearby_agencies(
        latitude=latitude,
        longitude=longitude,
        radius=radius,
        query=query,
    )


@router.get(
    "/search",
    response_model=GasAgenciesResponse,
    status_code=status.HTTP_200_OK,
    summary="Search LPG gas agencies by area or name",
)
async def search_gas_agencies(
    query: str = Query(
        ...,
        min_length=2,
        description="Area, city, or distributor name (e.g. 'Koramangala Bangalore')",
    ),
    latitude: float | None = Query(
        default=None,
        ge=-90.0,
        le=90.0,
        description="Optional anchor latitude",
    ),
    longitude: float | None = Query(
        default=None,
        ge=-180.0,
        le=180.0,
        description="Optional anchor longitude",
    ),
    radius: int = Query(
        default=10000,
        ge=500,
        le=50000,
        description="Search radius in meters",
    ),
):
    """
    Search for LPG agencies using a text query, with optional location bias.
    """
    # If coordinates not provided, default to a neutral anchor or use query directly
    lat = latitude if latitude is not None else 12.9716  # fallback center
    lng = longitude if longitude is not None else 77.5946

    return await gas_agency_service.get_nearby_agencies(
        latitude=lat,
        longitude=lng,
        radius=radius,
        query=f"LPG gas agency in {query}",
    )
