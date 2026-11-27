from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import engine, Base, get_db
from app.models import ride, report
from app.api import rides, users, reports

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(rides.router)
app.include_router(users.router)
app.include_router(reports.router)

@app.get("/")
def greet():
    return {"Message": "Welcome to the BITS Carpool Server!"}

@app.get("/api/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed",
        )
    return {"status": "ok", "database": "connected"}