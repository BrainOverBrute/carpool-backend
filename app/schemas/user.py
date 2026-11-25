from pydantic import BaseModel, Field

class ContactUpdate(BaseModel):
    # Accepts +919876543210 or 10-digit Indian mobile numbers starting with 6-9
    contact: str = Field(..., pattern=r"^(\+91)?[6-9]\d{9}$")