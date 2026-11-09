from fastapi import FastAPI
from app.database import engine
from app.models.ride import Base

app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get("/")
def greet():
    return {"Message": "Welcome to the BITS Carpool Server!"}