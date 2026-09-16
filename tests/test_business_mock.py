"""
Unit Tests for Business Logic Tier using Mock/Fake Data Layer.
Mandatory Deliverable:
"At least 5 unit tests for the Business Logic tier that use a fake/mock data source
(i.e., do not hit a real database)."

Verifies all required business rules:
- Title and Author cannot be empty.
- Publication Year must be a valid year (not in the future).
- ISBN must be exactly 10 or 13 digits.
- Quantity cannot be negative.
- A book cannot be checked out if quantity is already 0 (meaningful error, no crash).
- Check out decreases quantity by 1.
"""
from datetime import datetime
import pytest

from data.repositories.memory_repository import InMemoryBookRepository
from business.book_service import BookService
from business.exceptions import (
    ValidationError,
    OutOfStockError,
    DuplicateISBNError,
    BookNotFoundError,
)


@pytest.fixture
def mock_service():
    """Provides a BookService wired to a fake in-memory repository (NO DATABASE)."""
    fake_repo = InMemoryBookRepository()
    return BookService(repository=fake_repo)


def test_mock_add_book_success(mock_service):
    """Test 1: Successfully adding a book under valid business constraints."""
    book = mock_service.add_book(
        title="The Pragmatic Programmer",
        author="David Thomas, Andrew Hunt",
        isbn="978-0135957059",
        publication_year=2019,
        quantity=5,
    )
    assert book.id == 1
    assert book.title == "The Pragmatic Programmer"
    assert book.quantity == 5


def test_mock_rule1_title_and_author_cannot_be_empty(mock_service):
    """Test 2: Rule 1 - Title and Author cannot be empty."""
    # Empty title
    with pytest.raises(ValidationError, match="Title cannot be empty"):
        mock_service.add_book(
            title="   ",
            author="Valid Author",
            isbn="9780132350884",
            publication_year=2020,
            quantity=1,
        )

    # Empty author
    with pytest.raises(ValidationError, match="Author cannot be empty"):
        mock_service.add_book(
            title="Valid Title",
            author="",
            isbn="9780132350884",
            publication_year=2020,
            quantity=1,
        )


def test_mock_rule2_publication_year_not_in_future(mock_service):
    """Test 3: Rule 2 - Publication Year must not be in the future."""
    future_year = datetime.utcnow().year + 5
    with pytest.raises(ValidationError, match="Publication Year cannot be in the future"):
        mock_service.add_book(
            title="Future Tech",
            author="Time Traveler",
            isbn="9780132350884",
            publication_year=future_year,
            quantity=1,
        )


def test_mock_rule3_isbn_must_be_10_or_13_digits(mock_service):
    """Test 4: Rule 3 - ISBN must be exactly 10 or 13 digits."""
    # Too short (9 digits)
    with pytest.raises(ValidationError, match="ISBN must be exactly 10 or 13 digits"):
        mock_service.add_book("Book", "Author", "123456789", 2020, 1)

    # Invalid characters (letters)
    with pytest.raises(ValidationError, match="ISBN must be exactly 10 or 13 digits"):
        mock_service.add_book("Book", "Author", "12345ABCDE", 2020, 1)

    # 10 digits (Valid)
    b10 = mock_service.add_book("Book 10", "Author", "0132350882", 2008, 1)
    assert b10.isbn == "0132350882"

    # 13 digits with hyphens (Valid)
    b13 = mock_service.add_book("Book 13", "Author", "978-0-13-235088-4", 2008, 1)
    assert b13.isbn == "9780132350884"


def test_mock_rule4_quantity_cannot_be_negative(mock_service):
    """Test 5: Rule 4 - Quantity cannot be negative."""
    with pytest.raises(ValidationError, match="Quantity cannot be negative"):
        mock_service.add_book(
            title="Negative Book",
            author="Author",
            isbn="9780132350884",
            publication_year=2020,
            quantity=-1,
        )


def test_mock_rule5_checkout_fails_when_quantity_is_zero(mock_service):
    """Test 6: Rule 5 - A book cannot be checked out if quantity is already 0."""
    book = mock_service.add_book(
        title="Limited Edition",
        author="Collector",
        isbn="9780132350884",
        publication_year=2021,
        quantity=0,  # Starts with 0 copies
    )

    # Check out must raise OutOfStockError with a meaningful message, not crash
    with pytest.raises(OutOfStockError, match="quantity is already 0"):
        mock_service.checkout_book(book.id)


def test_mock_checkout_decreases_quantity_by_one(mock_service):
    """Test 7: Check out decreases quantity by 1."""
    book = mock_service.add_book(
        title="Clean Architecture",
        author="Robert C. Martin",
        isbn="9780134494166",
        publication_year=2017,
        quantity=3,
    )
    assert book.quantity == 3

    # Check out 1
    updated = mock_service.checkout_book(book.id)
    assert updated.quantity == 2

    # Check out another
    updated2 = mock_service.checkout_book(book.id)
    assert updated2.quantity == 1


def test_mock_duplicate_isbn_rejected(mock_service):
    """Test 8: Duplicate ISBN is rejected."""
    mock_service.add_book("First Book", "Author", "9780132350884", 2010, 1)
    with pytest.raises(DuplicateISBNError):
        mock_service.add_book("Second Book", "Another Author", "9780132350884", 2012, 1)


def test_mock_search_books_partial_match(mock_service):
    """Test 9: Partial match search by title or author."""
    mock_service.add_book("Refactoring", "Martin Fowler", "9780201485677", 1999, 2)
    mock_service.add_book("Domain-Driven Design", "Eric Evans", "9780321125217", 2003, 1)

    # Search by partial title
    results = mock_service.search_books("refactor")
    assert len(results) == 1
    assert results[0].title == "Refactoring"

    # Search by partial author
    results2 = mock_service.search_books("evans")
    assert len(results2) == 1
    assert results2[0].author == "Eric Evans"
