"""
Data Tier: SQLAlchemy ORM Domain Entity Models.
Defines schema definitions for books, members, and borrowing transactions.
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship

from data.database import Base


class MembershipType(str, Enum):
    STUDENT = "STUDENT"
    FACULTY = "FACULTY"
    GENERAL = "GENERAL"


class BorrowStatus(str, Enum):
    BORROWED = "BORROWED"
    RETURNED = "RETURNED"


class Book(Base):
    """Book model representing catalog items in the library."""
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    isbn = Column(String(32), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False, index=True)
    author = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    total_copies = Column(Integer, nullable=False, default=1)
    available_copies = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    borrow_records = relationship("BorrowRecord", back_populates="book", cascade="all, delete-orphan")


class Member(Base):
    """Member model representing library card holders."""
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    membership_type = Column(SQLEnum(MembershipType), nullable=False, default=MembershipType.STUDENT)
    max_borrow_limit = Column(Integer, nullable=False, default=3)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    borrow_records = relationship("BorrowRecord", back_populates="member", cascade="all, delete-orphan")


class BorrowRecord(Base):
    """BorrowRecord model tracking checkouts, due dates, returns, and fines."""
    __tablename__ = "borrow_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    borrow_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    due_date = Column(DateTime, nullable=False)
    return_date = Column(DateTime, nullable=True)
    fine_amount = Column(Float, nullable=False, default=0.0)
    status = Column(SQLEnum(BorrowStatus), nullable=False, default=BorrowStatus.BORROWED, index=True)

    book = relationship("Book", back_populates="borrow_records")
    member = relationship("Member", back_populates="borrow_records")
