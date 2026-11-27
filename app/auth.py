import os
import jwt
from dotenv import load_dotenv
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.ride import User

load_dotenv()

token_bearer = HTTPBearer()

CLERK_FRONTEND_API = os.getenv("CLERK_FRONTEND_API")
if not CLERK_FRONTEND_API:
    raise ValueError("CLERK_FRONTEND_API is not set in .env")

JWKS_URL = f"{CLERK_FRONTEND_API}/.well-known/jwks.json"
jwks_client = PyJWKClient(JWKS_URL)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(token_bearer),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials

    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=CLERK_FRONTEND_API,
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
        )

    # Check if the user exists in our database
    user = db.query(User).filter(User.id == clerk_id).first()

    # If they are a new Clerk user, create their DB row right now
    if not user:
        email = payload.get("email")
        if not email or not email.endswith("@goa.bits-pilani.ac.in"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only BITS Goa emails are allowed",
            )

        # Populate required fields from Clerk claims; contact number can be added
        # via the PUT /api/users/me endpoint later.
        user = User(
            id=clerk_id,
            first_name=payload.get("first_name") or "BITSian",
            last_name=payload.get("last_name") or "",
            email=email,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    if user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    return user