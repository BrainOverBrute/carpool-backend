from fastapi import FastAPI
from app.database import engine, Base
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