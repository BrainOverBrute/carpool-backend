from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.ride import Ride, User, RideMember

from app.schemas.ride import PoolCreate, PoolResponse, JoinRequest, RideListItem, RideListResponse, MembershipActionRequest, MembershipActionResponse

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

@router.get("/", response_model = RideListResponse)
def list_rides(
    origin: str | None = Query(default=None, description="Filter by origin"),
    destination: str | None = Query(default=None, description="Filter by destination"),
    target_time: AwareDatetime | None = Query(default=None, description="Target arrival time (±4h window)"),
    hide_full: bool = Query(default=True, description="Hide rides with 0 available seats"),
    ride_id: str | None = Query(default=None, description="Filter by a specific ride ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_time = datetime.now(timezone.utc)
    member_count_expr = func.count(RideMember.id)

    query = (
        db.query(
            Ride,
            member_count_expr.label("member_count"),
        )
        .outerjoin(RideMember, Ride.id == RideMember.ride_id)
        .filter(
            Ride.status == "active",
            Ride.is_deleted.is_(False),
            Ride.expected_arrival_time > current_time,
        )
    ) 

    if origin:
        query = query.filter(Ride.origin.ilike(f"%{origin.strip()}%"))

    if destination:
        query = query.filter(Ride.destination.ilike(f"%{destination.strip()}%"))

    if target_time:
        window_start = target_time - timedelta(hours=4)
        window_end = target_time + timedelta(hours=4)
        query = query.filter(
            Ride.expected_arrival_time >= window_start,
            Ride.expected_arrival_time <= window_end,
        )

    if ride_id: query = query.filter(Ride.id == ride_id)

    query = query.group_by(Ride.id)

    if hide_full and not ride_id:
        query = query.having(Ride.total_accommodation - member_count_expr > 0)

    rows = query.order_by(Ride.expected_arrival_time.asc()).all()

    ride_ids = [ride.id for ride, _ in rows]
    members_by_ride: dict[str, list[tuple[RideMember, User]]] = {rid: [] for rid in ride_ids}

    if ride_ids:
        member_rows = (
            db.query(RideMember, User)
            .join(User, RideMember.user_id == User.id)
            .filter(RideMember.ride_id.in_(ride_ids))
            .all()
        )
        for member, user in member_rows:
            members_by_ride[member.ride_id].append((member, user))

    results = []

    for ride, member_count in rows:
        ride_members = members_by_ride[ride.id]
        is_member = False

        for member, _ in ride_members:
            if member.user_id == current_user.id:
                is_member = True
                break

        is_owner = ride.ride_owner == current_user.id

        member_list = [
            RideMemberInfo(
                user_id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                role=member.role,
                contact=user.contact if is_member else None,
                luggage_brought=member.luggage_brought,
            )
            for member, user in ride_members
        ]

        available_seats = ride.total_accommodation - member_count
        item = RideListItem(
            id=ride.id,
            ride_owner=ride.ride_owner,
            origin=ride.origin,
            destination=ride.destination,
            expected_arrival_time=ride.expected_arrival_time,
            total_accommodation=ride.total_accommodation,
            available_seats=max(0, available_seats),
            expected_luggage=ride.expected_luggage,
            total_ride_fare=ride.total_ride_fare,
            driver_name=ride.driver_name if is_member else None,
            driver_number=ride.driver_number if is_member else None,
            is_ticketed=ride.is_ticketed,
            is_member=is_member,
            is_owner=is_owner,
            members=member_list,
        )
        results.append(item)

    return RideListResponse(
        total=len(results),
        rides=results,
    )

@router.put("/{ride_id}/membership", response_model = MembershipActionResponse)
def update_membership(
    ride_id: str,
    payload: MembershipActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. Fetch and row-lock the active ride
    ride = (
        db.query(Ride)
        .filter(
            Ride.id == ride_id,
            Ride.status == "active",
            Ride.is_deleted.is_(False),
        )
        .with_for_update()
        .first()
    )
    if not ride:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active ride not found")

    removed_user_id: str | None = None

    # 2. Handle the 3 actions: "cancel", "kick", "leave"
    if payload.action == "cancel":
        if current_user.id == ride.ride_owner:
            ride.status = "cancelled"
            ride.is_deleted = True
            ride.expected_luggage = 0

            db.query(RideMember).filter(RideMember.ride_id == ride.id).delete()
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can not cancel a ride unless you're the owner")

    elif payload.action == "kick":
        # TODO: Verify current_user.id == ride.ride_owner (else 403)
        if current_user.id == ride.ride_owner:
            if not payload.user_id:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="No user id found to kick")
            if payload.user_id==current_user.id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Can not kick yourself")

            member = db.query(RideMember).filter(RideMember.ride_id == ride.id,RideMember.user_id == payload.user_id).first()

            if not member:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user is not a member of this ride")

            ride.expected_luggage = max(0, ride.expected_luggage - member.luggage_brought)
            db.delete(member)
            removed_user_id = payload.user_id
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can not kick someone unless you're the owner")

    elif payload.action == "leave":
        # TODO: Find current_user's RideMember row (else 404), subtract luggage_brought, delete row
        member = db.query(RideMember).filter(RideMember.ride_id == ride.id, RideMember.user_id == current_user.id).first()
        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You are not a member of this ride",
            )

        ride.expected_luggage = max(0, ride.expected_luggage - member.luggage_brought)
        db.delete(member)
        db.flush()

        remaining_members = (
            db.query(RideMember)
            .filter(RideMember.ride_id == ride.id)
            .order_by(RideMember.joined_at.asc())
            .all()
        )

        if not remaining_members:
            ride.is_deleted = True
            ride.status = "cancelled"

        elif current_user.id == ride.ride_owner:
            ride.ride_owner = remaining_members[0].user_id
            remaining_members[0].role = "owner"

    # 3. Compute updated available_seats and commit
    remaining_count = db.query(func.count(RideMember.id)).filter(RideMember.ride_id == ride.id).scalar() or 0
    available_seats = max(0, ride.total_accommodation - remaining_count)

    db.commit()

    return MembershipActionResponse(
        ride_id=ride.id,
        action=payload.action,
        ride_status=ride.status,
        available_seats=available_seats,
        removed_user_id=removed_user_id,
    )