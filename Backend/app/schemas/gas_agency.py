from pydantic import BaseModel, Field


class GasAgency(BaseModel):
    id: str = Field(..., description="Unique Google Place ID or agency identifier")
    name: str = Field(..., description="Agency or distributor business name")
    address: str = Field(..., description="Full formatted address of the agency")
    latitude: float = Field(..., description="Geographical latitude coordinate")
    longitude: float = Field(..., description="Geographical longitude coordinate")
    distance_km: float = Field(..., description="Distance in kilometers from user location")
    phone_number: str | None = Field(default=None, description="National or international contact phone number")
    google_maps_url: str = Field(..., description="Google Maps URL for directions or location")
    rating: float | None = Field(default=None, description="Average user rating (e.g. 4.2)")
    user_ratings_total: int | None = Field(default=None, description="Total count of user reviews")


class UserLocation(BaseModel):
    latitude: float
    longitude: float


class GasAgenciesResponse(BaseModel):
    success: bool = True
    count: int = Field(..., description="Number of gas agencies returned")
    radius_meters: int = Field(..., description="Search radius in meters")
    user_location: UserLocation | None = None
    agencies: list[GasAgency] = Field(default_factory=list, description="List of nearby gas agencies sorted by distance")
    message: str | None = None
