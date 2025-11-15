from sqlalchemy import create_engine
from app.db.models import Base

DATABASE_URL = "sqlite:///./app_data.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

def init_db():
    Base.metadata.create_all(bind=engine)






# # app/db/session.py
# import os
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from app.db.models import Base

# DB_URL = os.getenv("DATABASE_URL", "sqlite:///./app_data.db")
# # For SQLite, allow check_same_thread for FastAPI concurrency
# engine = create_engine(
#     DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {}
# )
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# def init_db():
#     Base.metadata.create_all(bind=engine)
