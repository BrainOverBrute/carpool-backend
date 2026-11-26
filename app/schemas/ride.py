from pydantic import BaseModel, AwareDatetime, Field

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

class RideMemberInfo(BaseModel):
    user_id: str = Field(..., description="Unique identifier of the member")
    first_name: str = Field(..., description="First name of the member")
    last_name: str = Field(..., description="Last name of the member")
    role: str = Field(..., description="Role in the pool (e.g., owner, member)")
    contact: str | None = Field(default=None, description="Contact number (visible only to pool members)")
    luggage_brought: int = Field(..., ge=0, le=4, description="Number of large bags brought by this member")

class RideListItem(BaseModel):
    id: str
    ride_owner: str
    origin: str
    destination: str
    expected_arrival_time: AwareDatetime
    total_accommodation: int
    available_seats: int
    expected_luggage: int
    total_ride_fare: int | None = None
    driver_name: str | None = None
    driver_number: str | None = None
    is_ticketed: bool
    is_member: bool
    is_owner: bool
    members: list[RideMemberInfo]

class RideListResponse(BaseModel):
    total: int = Field(..., ge=0, description="Number of matching rides returned")
    rides: list[RideListItem] = Field(..., description="List of matching rides")