"""
Unit Tests for Business Tier: Domain Services and Rules.
Verifies business logic, constraints, validation, and domain exceptions.
"""
from datetime import datetime, timedelta
import pytest

from data.models import MembershipType, BorrowRecord, BorrowStatus
from data.repositories.book_repository import BookRepository
from data.repositories.member_repository import MemberRepository
from data.repositories.borrow_repository import BorrowRepository
from business.services.book_service import BookService
from business.services.member_service import MemberService
from business.services.borrow_service import BorrowService
from business.exceptions import (
    BookNotFoundError,
    DuplicateISBNError,
    InvalidBookDataError,
    BookNotAvailableError,
    BookHasActiveLoansError,
    MemberNotFoundError,
    DuplicateEmailError,
    MemberInactiveError,
    BorrowLimitExceededError,
    BookAlreadyReturnedError,
)


@pytest.fixture
def services(db_session):
    """Instantiates business tier services backed by current test session."""
    book_repo = BookRepository(db_session)
    member_repo = MemberRepository(db_session)
    borrow_repo = BorrowRepository(db_session)
    return (
        BookService(book_repo, borrow_repo),
        MemberService(member_repo, borrow_repo),
        BorrowService(book_repo, member_repo, borrow_repo),
    )


class TestBookService:
    def test_add_book_success(self, services):
        book_svc, _, _ = services
        book = book_svc.add_book(
            title="Refactoring",
            author="Martin Fowler",
            isbn="978-0201485677",
            category="Software Engineering",
            total_copies=5,
        )
        assert book.id is not None
        assert book.available_copies == 5

    def test_add_duplicate_isbn_raises(self, services, sample_book):
        book_svc, _, _ = services
        with pytest.raises(DuplicateISBNError):
            book_svc.add_book(
                title="Duplicate",
                author="Someone",
                isbn=sample_book.isbn,
                category="General",
                total_copies=1,
            )

    def test_add_book_invalid_copies_raises(self, services):
        book_svc, _, _ = services
        with pytest.raises(InvalidBookDataError):
            book_svc.add_book(
                title="Invalid",
                author="Author",
                isbn="12345",
                category="General",
                total_copies=0,
            )

    def test_cannot_delete_book_with_active_loans(self, services, sample_book, sample_member):
        book_svc, _, borrow_svc = services
        borrow_svc.borrow_book(member_id=sample_member.id, book_id=sample_book.id)
        with pytest.raises(BookHasActiveLoansError):
            book_svc.delete_book(sample_book.id)


class TestMemberService:
    def test_register_member_success(self, services):
        _, member_svc, _ = services
        member = member_svc.register_member(
            name="Charlie",
            email="charlie@test.com",
            membership_type=MembershipType.FACULTY,
        )
        assert member.max_borrow_limit == 10
        assert member.is_active is True

    def test_register_duplicate_email_raises(self, services, sample_member):
        _, member_svc, _ = services
        with pytest.raises(DuplicateEmailError):
            member_svc.register_member(
                name="Duplicate",
                email=sample_member.email,
            )

    def test_invalid_email_raises(self, services):
        _, member_svc, _ = services
        with pytest.raises(InvalidBookDataError):
            member_svc.register_member(name="Bad", email="notanemail")

    def test_cannot_deactivate_member_with_active_loans(self, services, sample_book, sample_member):
        _, member_svc, borrow_svc = services
        borrow_svc.borrow_book(member_id=sample_member.id, book_id=sample_book.id)
        with pytest.raises(BookHasActiveLoansError):
            member_svc.update_member(sample_member.id, is_active=False)


class TestBorrowService:
    def test_borrow_success_decrements_copies(self, services, sample_book, sample_member):
        _, _, borrow_svc = services
        initial_copies = sample_book.available_copies
        record = borrow_svc.borrow_book(member_id=sample_member.id, book_id=sample_book.id, loan_days=14)
        assert record.id is not None
        assert record.status == BorrowStatus.BORROWED
        assert sample_book.available_copies == initial_copies - 1

    def test_borrow_zero_copies_raises(self, services, sample_book, sample_member):
        book_svc, _, borrow_svc = services
        sample_book.available_copies = 0
        with pytest.raises(BookNotAvailableError):
            borrow_svc.borrow_book(member_id=sample_member.id, book_id=sample_book.id)

    def test_borrow_exceeds_limit_raises(self, services, sample_book, sample_member, db_session):
        _, _, borrow_svc = services
        sample_member.max_borrow_limit = 1
        # First borrow should succeed
        borrow_svc.borrow_book(member_id=sample_member.id, book_id=sample_book.id)
        # Second borrow should exceed limit
        with pytest.raises(BorrowLimitExceededError):
            borrow_svc.borrow_book(member_id=sample_member.id, book_id=sample_book.id)

    def test_return_book_on_time_zero_fine(self, services, sample_book, sample_member):
        _, _, borrow_svc = services
        record = borrow_svc.borrow_book(member_id=sample_member.id, book_id=sample_book.id, loan_days=14)
        returned = borrow_svc.return_book(record_id=record.id, return_time=record.borrow_date + timedelta(days=5))
        assert returned.status == BorrowStatus.RETURNED
        assert returned.fine_amount == 0.0
        assert sample_book.available_copies == 3

    def test_return_book_overdue_calculates_fine(self, services, sample_book, sample_member):
        _, _, borrow_svc = services
        record = borrow_svc.borrow_book(member_id=sample_member.id, book_id=sample_book.id, loan_days=14)
        # Returned 17 days after checkout (3 days overdue)
        overdue_time = record.borrow_date + timedelta(days=17)
        returned = borrow_svc.return_book(record_id=record.id, return_time=overdue_time, daily_fine=1.50)
        assert returned.status == BorrowStatus.RETURNED
        assert returned.fine_amount == round(3 * 1.50, 2)

    def test_return_already_returned_raises(self, services, sample_book, sample_member):
        _, _, borrow_svc = services
        record = borrow_svc.borrow_book(member_id=sample_member.id, book_id=sample_book.id)
        borrow_svc.return_book(record.id)
        with pytest.raises(BookAlreadyReturnedError):
            borrow_svc.return_book(record.id)
