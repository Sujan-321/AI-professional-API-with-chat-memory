from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models import Booking


router = APIRouter()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic schema for request body
class BookingRequest(BaseModel):
    session_id: str
    name: str
    email: str
    date: str
    time: str


@router.post("/bookings")
def create_booking(data: BookingRequest, db: Session = Depends(get_db)):
    """
    Save manual or LLM-extracted booking data into SQLite.
    """

    booking = Booking(
        session_id=data.session_id,
        name=data.name,
        email=data.email,
        date=data.date,
        time=data.time,
    )

    db.add(booking)
    db.commit()
    db.refresh(booking)

    return {
        "status": "ok",
        "booking_id": booking.id
    }
