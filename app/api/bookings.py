# app/api/bookings.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.crud import create_booking

router = APIRouter()

class BookingIn(BaseModel):
    session_id: str | None = None
    name: str
    email: EmailStr
    date: str  # YYYY-MM-DD
    time: str  # HH:MM (24h)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/bookings")
def create_booking_endpoint(payload: BookingIn, db: Session = Depends(get_db)):
    booking = create_booking(
        db=db,
        session_id=payload.session_id,
        name=payload.name,
        email=payload.email,
        date=payload.date,
        time=payload.time,
    )
    return {"status": "ok", "booking_id": booking.id}
