from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import session
from app.models.ride import Ride, User, RideMember

from app.schemas.ride import PoolCreate
from app.schemas.ride import PoolResponse

router = APIRouter(
    prefix="/api/rides",
    tags=["Rides"]
)

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_pool(payload: PoolCreate, db: Session = Depends(get_db)):
    new_ride = Ride(ride_owner = payload.ride_owner, 
                    origin = payload.origin, 
                    destination = payload.destination, 
                    expected_arrival_time = payload.expected_arrival_time, 
                    total_accommodation = payload.total_accommodation,
                    expected_luggage = payload.expected_luggage)
    
    db.add(new_ride)
    db.commit()

    db.refresh(new_ride)
    return new_ride