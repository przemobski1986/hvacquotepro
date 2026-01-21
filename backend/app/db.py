from app.base import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings
db_url = settings.DATABASE_URL
if str(db_url).startswith("sqlite"):
    engine = create_engine(db_url, connect_args={"check_same_thread": False}, pool_pre_ping=True)
else:
    engine = create_engine(db_url, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
