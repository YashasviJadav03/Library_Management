"""
Data Tier: SQLAlchemy ORM Entities.
Handles only database schema and persistence mapping.
Contains NO validation logic and NO display logic.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from data.database import Base


class Book(Base):
    """
    Book database entity.
    Fields required by specification:
    - Title, Author, ISBN, Publication Year, Quantity
    """
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255), nullable=False)
    isbn = Column(String(32), unique=True, index=True, nullable=False)
    publication_year = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
