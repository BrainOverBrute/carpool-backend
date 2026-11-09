from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Ride(Base):
    __tablename__ = "rides"

    id = Column(Integer, primary_key=True, index=True)
    origin = Column(String)
    destination = Column(String)
    total_accommodation = Column(Integer)
    expected_luggage = Column(Integer)