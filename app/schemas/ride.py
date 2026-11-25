from pydantic import BaseModel, AwareDatetime, Field
from uuid import UUID

class PoolCreate(BaseModel):
    origin: str = Field(..., description="Starting location (e.g., Dabolim)")
    destination: str = Field(..., description="Ending location (e.g., Campus)")
    expected_arrival_time: AwareDatetime = Field(..., description="Target arrival time")
    total_accommodation: int = Field(..., ge=3, le=8, description="Total seats in the cab")
    expected_luggage: int = Field(..., ge=0, le=4, description="Number of large bags for the trunk")

class PoolResponse(BaseModel):
    ride_id: str = Field(..., description="Unique identifier of the ride")
    status: str = Field(..., description="Current status of the ride (e.g., active)")
    message: str = Field(..., description="Confirmation message")

class JoinRequest(BaseModel):
    expected_luggage: int = Field(..., ge=0, le=4)

class RideListItem(BaseModel):
    id: UUID
    origin: str
    destination: str
    expected_arrival_time: AwareDatetime
    total_accommodation: int
    available_seats: int
    expected_luggage: int
    total_ride_fare: float | None = None
    is_ticketed: bool

class RideListResponse(BaseModel):
    total: int = Field(..., ge=0, description="Number of matching rides returned")
    rides: list[RideListItem] = Field(..., description="List of matching rides")