from fastapi import FastAPI
from app.database import engine
from app.models.ride import Base

from app.api import rides, users

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(rides.router)
app.include_router(users.router)

@app.get("/")
def greet():
    return {"Message": "Welcome to the BITS Carpool Server!"}