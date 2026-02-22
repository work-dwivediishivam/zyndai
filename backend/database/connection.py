"""Database connection and session management."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

# Configure connection pool for Supabase's session mode limits
# - pool_size: Number of connections to keep open (default is 5)
# - max_overflow: Extra connections allowed beyond pool_size (default is 10)
# - pool_recycle: Close and recreate connections after this many seconds
# - pool_pre_ping: Test connections before using them
engine = create_engine(
    DATABASE_URL, 
    echo=False, 
    pool_pre_ping=True,
    pool_size=3,  # Keep 3 connections in the pool
    max_overflow=2,  # Allow up to 2 extra connections (total 5 max)
    pool_recycle=300  # Recycle connections every 5 minutes
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for FastAPI to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    from models.base import Base
    Base.metadata.create_all(bind=engine)
