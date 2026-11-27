import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from app.database import Base

class Report(Base):
    __tablename__ = "reports"
    __table_args__ = (
        UniqueConstraint("ride_id", "reporter_id", "reported_user_id", name="uq_ride_reporter_reported"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    ride_id = Column(String, ForeignKey("rides.id"), nullable=False, index=True)
    reporter_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    reported_user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    reason = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))