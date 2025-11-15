# app/db/crud.py
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db import models

def save_document_metadata(
    db: Session,
    file_name: str,
    file_type: str,
    number_of_chunks: int,
    vector_ids: Optional[List[str]] = None,
    user_id: Optional[str] = None,
    extra: Optional[dict] = None,
):
    doc = models.DocumentMeta(
        file_name=file_name,
        file_type=file_type,
        number_of_chunks=number_of_chunks,
        user_id=user_id,
        vector_ids=vector_ids or [],
        extra=extra or {},
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

def create_booking(
    db: Session,
    session_id: Optional[str],
    name: str,
    email: str,
    date: str,
    time: str,
):
    booking = models.InterviewBooking(
        session_id=session_id,
        name=name,
        email=email,
        date=date,
        time=time,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking
