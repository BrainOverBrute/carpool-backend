from pydantic import BaseModel, Field
from datetime import datetime

class PoolCreate(BaseModel):
    origin: str = Field(..., description="Starting location (e.g., Dabolim)")
    destination: str = Field(..., description="Ending location (e.g., Campus)")
    expected_arrival_time: AwareDatetime = Field(..., description="Target arrival time")
    total_accommodation: int = Field(..., ge=3, le=8, description="Total seats in the cab")
    expected_luggage: int = Field(..., ge=0, le=4, description="Number of large bags for the trunk")

class PoolResponse(BaseModel):
    ride_id: str
    status: str
    message: str

class JoinRequest(BaseModel):
    expected_luggage: int = Field(..., ge=0, le=4)