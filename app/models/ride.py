import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda:str(uuid.uuid4()), index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    contact = Column(String)
    reported_fake_count = Column(Integer, default=0)
    is_deleted = Column(Boolean, default=False)

    rides_owned = relationship("Ride", back_populates="owner")
    rides_joined = relationship("RideMember", back_populates="user")


class Ride(Base):
    __tablename__ = "rides"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    ride_owner = Column(String, ForeignKey("users.id"))
    origin = Column(String)
    destination = Column(String)
    expected_arrival_time = Column(DateTime)
    total_accommodation = Column(Integer)
    total_ride_fare = Column(Integer, nullable=True)
    expected_luggage = Column(Integer, default=0)
    is_ticketed = Column(Boolean, default=False)
    status = Column(String, default="active")
    is_deleted = Column(Boolean, default=False)
    driver_name = Column(String, nullable=True)
    driver_number = Column(String, nullable=True)

    owner = relationship("User", back_populates="rides_owned")
    members = relationship("RideMember", back_populates="ride")


class RideMember(Base):
    __tablename__ = "ride_members"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    ride_id = Column(String, ForeignKey("rides.id"))
    user_id = Column(String, ForeignKey("users.id"))
    joined_at = Column(DateTime, default=datetime.utcnow)

    role = Column(String)
    luggage_brought = Column(Integer, default=0)
    
    user = relationship("User", back_populates="rides_joined")
    ride = relationship("Ride", back_populates="members")