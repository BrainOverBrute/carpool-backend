from pydantic import BaseModel, Field

class ReportCreate(BaseModel):
    reported_user_id: str
    ride_id: str
    reason: str

class ReportResponse(BaseModel):
    report_id: str
    ride_id: str
    reported_user_id: str
    message: str
    
