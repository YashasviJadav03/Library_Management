"""
Data Tier: Database Configuration and Session Management.
Manages database connection and session creation using SQLAlchemy.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Generator

# Database URL defaults to local SQLite file, can be overridden via environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./library.db")

# For SQLite, check_same_thread=False allows multi-threaded requests in FastAPI
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency provider for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Creates database tables if they do not exist."""
    Base.metadata.create_all(bind=engine)
