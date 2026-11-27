from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.report import Report
from app.models.ride import Ride, User, RideMember

from app.schemas.report import ReportCreate, ReportResponse

from app.auth import get_current_user

from datetime import datetime, timezone, timedelta

router = APIRouter(
    prefix="/api",
    tags=["Reports"]
)

@router.post("/reports", status_code=status.HTTP_201_CREATED, response_model=ReportResponse)
def report_user(
    payload: ReportCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if payload.reported_user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Can not report yourself",
        )

    ride = db.query(Ride).filter(Ride.id == payload.ride_id).first()
    if not ride:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ride not found",
        )
    
    shared_count = (
        db.query(func.count(RideMember.id))
        .filter(
            RideMember.ride_id == payload.ride_id,
            RideMember.user_id.in_([current_user.id, payload.reported_user_id]),
        )
        .scalar()
        or 0
    )

    if shared_count != 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Both users must be members of the shared ride",
        )

    prev_reports = (
        db.query(Report)
        .filter(Report.reporter_id == current_user.id,
                Report.ride_id == payload.ride_id,
                Report.reported_user_id == payload.reported_user_id)
        .first()
    )

    if prev_reports.reported_user_id == payload.reported_user_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already Reported",
        )

    new_report = Report(
        ride_id = payload.ride_id,
        reporter_id = current_user.id,
        reported_user_id = payload.reported_user_id,
        reason = payload.reason
    )

    db.add(new_report)

    reported_user = (
        db.query(User)
        .filter(User.id == payload.reported_user_id)
        .with_for_update()
        .first()
    )
    if not reported_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reported user not found",
        )

    reported_user.reported_fake_count = (reported_user.reported_fake_count or 0) + 1
    
    db.commit()
    db.refresh(new_report)

    return ReportResponse(
        report_id=new_report.id,
        ride_id=new_report.ride_id,
        reported_user_id=new_report.reported_user_id,
        message="Report submitted successfully",
    )