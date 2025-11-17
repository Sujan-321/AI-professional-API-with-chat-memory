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