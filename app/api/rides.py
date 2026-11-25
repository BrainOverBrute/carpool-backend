from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.ride import Ride, User, RideMember

from app.schemas.ride import PoolCreate,PoolResponse,JoinRequest

from app.auth import get_current_user

from datetime import datetime, timezone, timedelta

router = APIRouter(
    prefix="/api/rides",
    tags=["Rides"]
)

ALLOWED_LOCATIONS = {"Campus", "Dabolim", "Mopa", "Madgaon", "Verna", "Vasco", "Thivim", "Karmali"}

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_pool(
    payload: PoolCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.contact:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please add your mobile number first.",
        )

    # Validation on Origin and Destination
    if payload.origin not in ALLOWED_LOCATIONS or payload.destination not in ALLOWED_LOCATIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Origin and destination must be one of: " + ", ".join(sorted(ALLOWED_LOCATIONS)),
        )

    if payload.origin == payload.destination:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Origin and destination can't be the same.",
        )

    if payload.origin != "Campus" and payload.destination != "Campus":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="One of the endpoints must be Campus"
        )

    current_time = datetime.now(timezone.utc)

    # Validation on expected_arrival_time

    if payload.expected_arrival_time < current_time + timedelta(minutes=30):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="INVALID_ARRIVAL_TIME"
        )

    # Do not allow a second ride within a time period for same user

    window_start = payload.expected_arrival_time - timedelta(hours=24)
    window_end = payload.expected_arrival_time + timedelta(hours=24)

    # 1. Query the database for the user's upcoming active rides
    # We join the Ride and RideMember tables to find rides this specific user is part of.
    user_active_rides = (
        db.query(Ride)
        .join(RideMember, Ride.id == RideMember.ride_id)
        .filter(
            RideMember.user_id == current_user.id,
            Ride.status == "active",
            Ride.is_deleted.is_(False),
            Ride.expected_arrival_time > current_time # Only count future rides
        )
        .all()
    )

    # 2. Check Spec Rule: Max 2 active upcoming rides total
    if len(user_active_rides) >= 2:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have reached the maximum limit of 2 active upcoming rides."
        )

    # 3. Check Custom Rule: No overlapping rides within the time window
    for existing_ride in user_active_rides:
        if window_start <= existing_ride.expected_arrival_time <= window_end:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"You already have a ride scheduled around {existing_ride.expected_arrival_time.strftime('%d %b, %H:%M')}."
            )


    new_ride = Ride(ride_owner = current_user.id,
                    origin = payload.origin,
                    destination = payload.destination, 
                    expected_arrival_time = payload.expected_arrival_time, 
                    total_accommodation = payload.total_accommodation,
                    expected_luggage = payload.expected_luggage)
    
    db.add(new_ride)

    db.flush()

    new_member = RideMember(
        ride_id=new_ride.id,
        user_id=current_user.id,
        role="owner",
        luggage_brought=payload.expected_luggage
    )
    db.add(new_member)

    db.commit()

    db.refresh(new_ride)

    return {
        "status": True,
        "msg": {
            "ride_id": new_ride.id,
            "status": "active",
            "is_ticketed": False
        }
    }


@router.post("/{ride_id}/join")
def join_pool(ride_id: str, 
              payload: JoinRequest, 
              db: Session = Depends(get_db), 
              current_user: User = Depends(get_current_user)):
    ride = db.query(Ride).filter(Ride.id == ride_id, Ride.is_deleted.is_(False)).first()
    
    if not ride:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found.")

    current_time = datetime.now(timezone.utc)
    if ride.status != "active" or ride.expected_arrival_time <= current_time:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="RIDE_CLOSED"
        )
    
    if not current_user.contact:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please add your mobile number first."
        )

    # Check if the user has already joined this ride
    existing_member = (
        db.query(RideMember)
        .filter(RideMember.ride_id == ride.id, RideMember.user_id == current_user.id)
        .first()
    )
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="ALREADY_JOINED"
        )

    # Do not allow user to join a second ride within a time period

    window_start = ride.expected_arrival_time - timedelta(hours=24)
    window_end = ride.expected_arrival_time + timedelta(hours=24)

    # 1. Query the database for the user's upcoming active rides
    # We join the Ride and RideMember tables to find rides this specific user is part of.
    user_active_rides = (
        db.query(Ride)
        .join(RideMember, Ride.id == RideMember.ride_id)
        .filter(
            RideMember.user_id == current_user.id,
            Ride.status == "active",
            Ride.is_deleted.is_(False),
            Ride.expected_arrival_time > current_time # Only count future rides
        )
        .all()
    )

    # 2. Check Spec Rule: Max 2 active upcoming rides total
    if len(user_active_rides) >= 2:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have reached the maximum limit of 2 active upcoming rides."
        )

    # 3. Check Custom Rule: No overlapping rides within the time window
    for existing_ride in user_active_rides:
        if window_start <= existing_ride.expected_arrival_time <= window_end:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"You already have a ride scheduled around {existing_ride.expected_arrival_time.strftime('%d %b, %H:%M')}."
            )


    member_count, current_luggage = (
        db.query(
            func.count(RideMember.id),
            func.coalesce(func.sum(RideMember.luggage_brought), 0),
        )
        .filter(RideMember.ride_id == ride.id)
        .one()
    )

    available_seats = ride.total_accommodation - member_count

    if available_seats <= 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="RIDE_FULL"
        )

    new_member = RideMember(
        ride_id=ride.id,
        user_id=current_user.id,
        role = "member",
        luggage_brought=payload.expected_luggage
    )

    ride.expected_luggage = current_luggage + payload.expected_luggage

    db.add(new_member)
    db.commit()

    return {
        "status": True,
        "msg": {
            "ride_id": str(ride.id),
            "remaining_seats": available_seats - 1,
            "total_luggage": current_luggage + payload.expected_luggage
        }
    }