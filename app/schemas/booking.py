from pydantic import BaseModel

class BookingCreate(BaseModel):
    session_id: str
    name: str
    email: str
    date: str
    time: str

class BookingResponse(BaseModel):
    id: int
    session_id: str
    name: str
    email: str
    date: str
    time: str

    class Config:
        from_attributes = True
