import os
import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.ride import User 

token_bearer = HTTPBearer()

CLERK_FRONTEND_API = os.getenv("CLERK_FRONTEND_API")
JWKS_URL = f"{CLERK_FRONTEND_API}/.well-known/jwks.json"
jwks_client = PyJWKClient(JWKS_URL)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(token_bearer),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(token, signing_key.key, algorithms=["RS256"])
        clerk_id = payload.get("sub")
        
        # Check if the user exists in our database
        user = db.query(User).filter(User.id == clerk_id).first()
        
        # If they are a new Clerk user, create their DB row right now
        if not user:
            # We only have their ID right now. They can update other details 
            # (like contact number or name) via a separate PUT endpoint later.
            user = User(id=clerk_id) 
            db.add(user)
            db.commit()
            db.refresh(user)
            
        return user
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")