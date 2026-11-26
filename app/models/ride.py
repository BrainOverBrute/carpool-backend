import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda:str(uuid.uuid4()), index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    contact = Column(String)
    reported_fake_count = Column(Integer, default=0)
    is_deleted = Column(Boolean, default=False)

    rides_owned = relationship("Ride", back_populates="owner")
    rides_joined = relationship("RideMember", back_populates="user")


class Ride(Base):
    __tablename__ = "rides"
    __table_args__ = (
        CheckConstraint("total_accommodation BETWEEN 3 AND 8", name="ck_accommodation"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    ride_owner = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    expected_arrival_time = Column(DateTime(timezone=True), nullable=False)
    total_accommodation = Column(Integer, nullable=False)
    total_ride_fare = Column(Integer, nullable=True)
    expected_luggage = Column(Integer, default=0)
    is_ticketed = Column(Boolean, default=False)
    status = Column(String, default="active")
    is_deleted = Column(Boolean, default=False)
    driver_name = Column(String, nullable=True)
    driver_number = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="rides_owned")
    members = relationship("RideMember", back_populates="ride")


class RideMember(Base):
    __tablename__ = "ride_members"
    __table_args__ = (
        UniqueConstraint("ride_id", "user_id", name="uq_ride_user"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    ride_id = Column(String, ForeignKey("rides.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    role = Column(String)
    luggage_brought = Column(Integer, default=0)
    
    user = relationship("User", back_populates="rides_joined")
    ride = relationship("Ride", back_populates="members")