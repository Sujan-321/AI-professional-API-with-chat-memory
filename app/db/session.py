from sqlalchemy import create_engine
from app.db.models import Base

DATABASE_URL = "sqlite:///./app_data.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

def init_db():
    Base.metadata.create_all(bind=engine)


