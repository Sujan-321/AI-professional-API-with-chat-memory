from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    filetype = Column(String)
    upload_date = Column(DateTime, default=datetime.utcnow)
    chunk_strategy = Column(String)
    number_of_chunks = Column(Integer)
    vector_ids = Column(String)


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String)
    name = Column(String)
    email = Column(String)
    date = Column(String)
    time = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)







# # app/db/models.py
# from datetime import datetime
# from sqlalchemy import (
#     Column,
#     Integer,
#     String,
#     DateTime,
#     Text,
#     JSON,
#     ForeignKey,
# )
# from sqlalchemy.orm import declarative_base
# from pydantic import BaseModel



# Base = declarative_base()

# class DocumentMeta(Base):
#     __tablename__ = "document_meta"

#     id = Column(Integer, primary_key=True, index=True)
#     file_name = Column(String, nullable=False)
#     file_type = Column(String, nullable=False)
#     number_of_chunks = Column(Integer, nullable=False, default=0)
#     uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
#     user_id = Column(String, nullable=True)
#     # store vector IDs as JSON list; SQLite supports text but SQLAlchemy JSON will serialize
#     vector_ids = Column(JSON, nullable=True)
#     extra = Column(JSON, nullable=True)  # any extra metadata (pages, size...)

#     def to_dict(self):
#         return {
#             "id": self.id,
#             "file_name": self.file_name,
#             "file_type": self.file_type,
#             "number_of_chunks": self.number_of_chunks,
#             "uploaded_at": self.uploaded_at.isoformat(),
#             "user_id": self.user_id,
#             "vector_ids": self.vector_ids,
#             "extra": self.extra,
#         }

# class InterviewBooking(Base):
#     __tablename__ = "interview_booking"

#     id = Column(Integer, primary_key=True, index=True)
#     session_id = Column(String, nullable=True, index=True)
#     name = Column(String, nullable=False)
#     email = Column(String, nullable=False)
#     date = Column(String, nullable=False)   # YYYY-MM-DD
#     time = Column(String, nullable=False)   # HH:MM (24h)
#     created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# class BookingCreate(BaseModel):
#     session_id: str
#     name: str
#     email: str
#     date: str
#     time: str

# class BookingResponse(BaseModel):
#     id: int
#     session_id: str
#     name: str
#     email: str
#     date: str
#     time: str
#     created_at: str

#     class Config:
#         orm_mode = True
