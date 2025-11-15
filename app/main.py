from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# Routers
from app.api import document_ingestion, test_qdrant, test_redis
from app.api import router as api_router
from app.api.test_redis import router as test_redis_router
from app.api.conversate import router as conversate_router
from app.api.booking_api import router as booking_router

# DB imports
from app.db.session import init_db
from app.db.database import get_db
from app.db.models import Booking

# Schemas
from app.schemas.booking import BookingCreate, BookingResponse

load_dotenv()


# ---------------------------------------------------
# 🚀 Lifespan Event (Recommended by FastAPI v2)
# ---------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()   # create tables if not exist
    yield       # shutdown
    pass


# ---------------------------------------------------
# 🚀 Create APP (ONLY ONCE)
# ---------------------------------------------------
app = FastAPI(
    title="Palm Mind Backend",
    lifespan=lifespan
)


# ---------------------------------------------------
# 🚀 Include Routers
# ---------------------------------------------------
app.include_router(conversate_router, prefix="/api")
app.include_router(api_router, prefix="/api")
app.include_router(test_qdrant.router, prefix="/api/test")
app.include_router(test_redis.router, prefix="/api/test")
app.include_router(document_ingestion.router, prefix="/api/doc")
app.include_router(test_redis_router)
app.include_router(booking_router, prefix="/api")


# ---------------------------------------------------
# 🚀 Test Root
# ---------------------------------------------------
@app.get("/")
def root():
    return {"message": "Backend running successfully 🚀"}


# ---------------------------------------------------
# 🚀 Booking CRUD APIs
# ---------------------------------------------------
@app.get("/api/bookings", response_model=list[BookingResponse])
def get_all_bookings(db: Session = Depends(get_db)):
    return db.query(Booking).all()


@app.get("/api/bookings/{booking_id}", response_model=BookingResponse)
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@app.put("/api/bookings/{booking_id}", response_model=BookingResponse)
def update_booking(booking_id: int, updated: BookingCreate, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking.session_id = updated.session_id
    booking.name = updated.name
    booking.email = updated.email
    booking.date = updated.date
    booking.time = updated.time

    db.commit()
    db.refresh(booking)
    return booking


@app.delete("/api/bookings/{booking_id}")
def delete_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    db.delete(booking)
    db.commit()

    return {"status": "deleted", "booking_id": booking_id}
