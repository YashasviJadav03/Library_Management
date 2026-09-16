"""
Business Tier: Borrow Service.
Orchestrates borrowing transactions, checkout validations, return processing,
due-date tracking, and late-fee fine calculations.
"""
from datetime import datetime, timedelta
from typing import List, Optional
from data.models import BorrowRecord, BorrowStatus
from data.repositories.book_repository import BookRepository
from data.repositories.member_repository import MemberRepository
from data.repositories.borrow_repository import BorrowRepository
from business.exceptions import (
    BookNotFoundError,
    MemberNotFoundError,
    MemberInactiveError,
    BookNotAvailableError,
    BorrowLimitExceededError,
    BorrowRecordNotFoundError,
    BookAlreadyReturnedError,
)

DEFAULT_LOAN_DAYS = 14
DAILY_LATE_FINE = 1.00  # $1.00 per day overdue


class BorrowService:
    """Service implementing the business workflows for borrowing and returning books."""

    def __init__(
        self,
        book_repo: BookRepository,
        member_repo: MemberRepository,
        borrow_repo: BorrowRepository,
    ):
        self.book_repo = book_repo
        self.member_repo = member_repo
        self.borrow_repo = borrow_repo

    def borrow_book(
        self,
        member_id: int,
        book_id: int,
        loan_days: int = DEFAULT_LOAN_DAYS,
    ) -> BorrowRecord:
        """
        Processes a book checkout with business constraint validation:
        1. Member must exist and be active.
        2. Member active borrows must be strictly below their max limit.
        3. Book must exist and have at least 1 copy available.
        4. Decrements book available copies.
        5. Computes due date and persists the borrow record.
        """
        # Validate member
        member = self.member_repo.get_by_id(member_id)
        if not member:
            raise MemberNotFoundError(f"Member with ID {member_id} not found.")
        if not member.is_active:
            raise MemberInactiveError(f"Member '{member.name}' is inactive and cannot borrow books.")

        # Check borrow limit
        active_borrows = self.borrow_repo.get_active_borrows_by_member(member_id)
        if len(active_borrows) >= member.max_borrow_limit:
            raise BorrowLimitExceededError(
                f"Member '{member.name}' reached borrowing limit of {member.max_borrow_limit} books."
            )

        # Validate book availability
        book = self.book_repo.get_by_id(book_id)
        if not book:
            raise BookNotFoundError(f"Book with ID {book_id} not found.")
        if book.available_copies <= 0:
            raise BookNotAvailableError(
                f"Book '{book.title}' currently has 0 copies available for checkout."
            )

        # Decrement available copies
        book.available_copies -= 1
        self.book_repo.update(book)

        # Calculate loan window
        borrow_date = datetime.utcnow()
        due_date = borrow_date + timedelta(days=loan_days)

        record = BorrowRecord(
            book_id=book_id,
            member_id=member_id,
            borrow_date=borrow_date,
            due_date=due_date,
            status=BorrowStatus.BORROWED,
            fine_amount=0.0,
        )
        return self.borrow_repo.add(record)

    def return_book(
        self,
        record_id: int,
        return_time: Optional[datetime] = None,
        daily_fine: float = DAILY_LATE_FINE,
    ) -> BorrowRecord:
        """
        Processes a book return:
        1. Validates the borrow record exists and is in BORROWED status.
        2. Calculates overdue days past due_date.
        3. Computes late fine fee if overdue.
        4. Increments book available copies.
        5. Marks record as RETURNED.
        """
        record = self.borrow_repo.get_by_id(record_id)
        if not record:
            raise BorrowRecordNotFoundError(f"Borrow record {record_id} does not exist.")
        if record.status == BorrowStatus.RETURNED:
            raise BookAlreadyReturnedError(
                f"Borrow record {record_id} was already returned on {record.return_date}."
            )

        now = return_time or datetime.utcnow()
        record.return_date = now
        record.status = BorrowStatus.RETURNED

        # Calculate late fines
        if now > record.due_date:
            overdue_delta = now - record.due_date
            # Day count or fractional day rounded up to full day
            overdue_days = max(1, overdue_delta.days)
            record.fine_amount = round(overdue_days * daily_fine, 2)
        else:
            record.fine_amount = 0.0

        # Increment available copies back
        book = self.book_repo.get_by_id(record.book_id)
        if book:
            book.available_copies = min(book.total_copies, book.available_copies + 1)
            self.book_repo.update(book)

        return self.borrow_repo.update(record)

    def get_record(self, record_id: int) -> BorrowRecord:
        """Retrieves a single borrow record."""
        record = self.borrow_repo.get_by_id(record_id)
        if not record:
            raise BorrowRecordNotFoundError(f"Borrow record {record_id} not found.")
        return record

    def list_records(
        self,
        member_id: Optional[int] = None,
        book_id: Optional[int] = None,
        status: Optional[BorrowStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[BorrowRecord]:
        """Lists borrowing records with optional filtering."""
        return self.borrow_repo.list_records(
            member_id=member_id,
            book_id=book_id,
            status=status,
            skip=skip,
            limit=limit,
        )

    def get_member_active_borrows(self, member_id: int) -> List[BorrowRecord]:
        """Returns all currently active checkouts for a member."""
        # Ensure member exists
        member = self.member_repo.get_by_id(member_id)
        if not member:
            raise MemberNotFoundError(f"Member with ID {member_id} not found.")
        return self.borrow_repo.get_active_borrows_by_member(member_id)
