from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.ride import User
from app.schemas.user import ContactUpdate
from app.auth import get_current_user

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.put("/me")
def update_contact(
    payload: ContactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    current_user.contact = payload.contact
    db.commit()

    return {
        "status": True,
        "msg": {
            "has_contact": True
        }
    }