from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    
    rides_joined = relationship("RideMember", back_populates="user")


class Ride(Base):
    __tablename__ = "rides"

    id = Column(Integer, primary_key=True, index=True)
    origin = Column(String)
    destination = Column(String)
    expected_arrival_time = Column(DateTime)
    total_accommodation = Column(Integer)
    expected_luggage = Column(Integer)
    status = Column(String, default="active")

    members = relationship("RideMember", back_populates="ride")


class RideMember(Base):
    __tablename__ = "ride_members"

    id = Column(Integer, primary_key=True, index=True)
    ride_id = Column(Integer, ForeignKey("rides.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    role = Column(String)
    luggage_brought = Column(Integer)
    
    user = relationship("User", back_populates="rides_joined")
    ride = relationship("Ride", back_populates="members")