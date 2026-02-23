from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import DATABASE_URL
from app.models import Base

# Create engine
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_db_and_tables():
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)


def get_session():
    """Get a database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
