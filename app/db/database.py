from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

DATABASE_URL = "sqlite:///./app_data.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()











# from sqlalchemy import create_engine, Column, Integer, String, DateTime
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
# from datetime import datetime

# DATABASE_URL = "sqlite:///./app_data.db"

# engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
# SessionLocal = sessionmaker(bind=engine)
# Base = declarative_base()

# class Document(Base):
#     __tablename__ = "documents"
    
#     id = Column(Integer, primary_key=True, index=True)
#     filename = Column(String)
#     filetype = Column(String)
#     upload_date = Column(DateTime, default=datetime.utcnow)
#     chunk_strategy = Column(String)

#     # ✅ Add missing fields
#     number_of_chunks = Column(Integer)
#     vector_ids = Column(String)


# class Booking(Base):
#     __tablename__ = "bookings"

#     id = Column(Integer, primary_key=True, index=True)
#     session_id = Column(String)
#     name = Column(String)
#     email = Column(String)
#     date = Column(String)     # You can use Date type, but String is simpler
#     time = Column(String)     # Same reason as above
#     created_at = Column(DateTime, default=datetime.utcnow)


# Base.metadata.create_all(bind=engine)