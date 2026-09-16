"""
Data Tier: Borrow Repository.
Encapsulates all database operations and SQL queries for borrowing transactions.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from data.models import BorrowRecord, BorrowStatus


class BorrowRepository:
    """Repository handling database operations for BorrowRecord entities."""

    def __init__(self, db: Session):
        self.db = db

    def add(self, record: BorrowRecord) -> BorrowRecord:
        """Persists a new borrow transaction."""
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_by_id(self, record_id: int) -> Optional[BorrowRecord]:
        """Retrieves a borrow record by ID."""
        return self.db.query(BorrowRecord).filter(BorrowRecord.id == record_id).first()

    def get_active_borrows_by_member(self, member_id: int) -> List[BorrowRecord]:
        """Retrieves currently unreturned borrow records for a specific member."""
        return (
            self.db.query(BorrowRecord)
            .filter(
                BorrowRecord.member_id == member_id,
                BorrowRecord.status == BorrowStatus.BORROWED,
            )
            .all()
        )

    def get_active_borrows_by_book(self, book_id: int) -> List[BorrowRecord]:
        """Retrieves currently unreturned borrow records for a specific book."""
        return (
            self.db.query(BorrowRecord)
            .filter(
                BorrowRecord.book_id == book_id,
                BorrowRecord.status == BorrowStatus.BORROWED,
            )
            .all()
        )

    def list_records(
        self,
        member_id: Optional[int] = None,
        book_id: Optional[int] = None,
        status: Optional[BorrowStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[BorrowRecord]:
        """Retrieves paginated borrow records with optional filters."""
        query = self.db.query(BorrowRecord)
        if member_id is not None:
            query = query.filter(BorrowRecord.member_id == member_id)
        if book_id is not None:
            query = query.filter(BorrowRecord.book_id == book_id)
        if status is not None:
            query = query.filter(BorrowRecord.status == status)
        return query.order_by(BorrowRecord.borrow_date.desc()).offset(skip).limit(limit).all()

    def update(self, record: BorrowRecord) -> BorrowRecord:
        """Commits updates to an existing borrow record."""
        self.db.commit()
        self.db.refresh(record)
        return record
