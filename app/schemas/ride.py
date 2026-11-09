from pydantic import BaseModel, Field
from datetime import datetime

class PoolCreate(BaseModel):
    origin: str = Field(..., description="Starting location (e.g., Dabolim)")
    destination: str = Field(..., description="Ending location (e.g., Campus)")
    expected_arrival_time: datetime = Field(..., description="Target arrival time")
    total_accommodation: int = Field(..., ge=1, le=8, description="Total seats in the cab")
    expected_luggage: int = Field(..., ge=0, le=4, description="Number of large bags for the trunk")

class PoolResponse(BaseModel):
    ride_id: int
    status: str
    message: str