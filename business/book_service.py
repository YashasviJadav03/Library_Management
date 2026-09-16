"""
Business Tier: Book Service.
Encapsulates all domain validation rules and application workflows.
Layer Rules strictly obeyed:
- Contains ALL validation and business rules.
- NEVER imports database libraries directly (no sqlite3, no SQLAlchemy).
- Depends ONLY on the abstract IBookRepository interface.
"""
from datetime import datetime
from typing import List, Optional
import re

from data.models import Book
from data.repositories.interfaces import IBookRepository
from business.exceptions import (
    ValidationError,
    BookNotFoundError,
    OutOfStockError,
    DuplicateISBNError,
)


class BookService:
    """Business logic service for managing the library book collection."""

    def __init__(self, repository: IBookRepository):
        """Inject repository dependency (loosely coupled via interface)."""
        self.repository = repository

    # -----------------------------------------------------------------------
    # Business Validation Helpers (Strictly in the Business Tier)
    # -----------------------------------------------------------------------
    @staticmethod
    def _clean_isbn(isbn: str) -> str:
        """Removes formatting characters (hyphens, spaces) from ISBN."""
        return re.sub(r"[-\s]", "", isbn or "")

    def _validate_book_fields(
        self,
        title: str,
        author: str,
        isbn: str,
        publication_year: int,
        quantity: int,
    ) -> str:
        """
        Validates all business rules for book attributes:
        1. Title and Author cannot be empty.
        2. Publication Year must be a valid year (not in the future).
        3. ISBN must be exactly 10 or 13 digits.
        4. Quantity cannot be negative.
        """
        # Rule 1: Title and Author cannot be empty
        if not title or not title.strip():
            raise ValidationError("Title cannot be empty.")
        if not author or not author.strip():
            raise ValidationError("Author cannot be empty.")

        # Rule 2: Publication Year must be a valid year (not in the future)
        current_year = datetime.utcnow().year
        if not isinstance(publication_year, int) or publication_year < 1:
            raise ValidationError("Publication Year must be a valid positive year.")
        if publication_year > current_year:
            raise ValidationError(
                f"Publication Year cannot be in the future. "
                f"Given: {publication_year}, Current Year: {current_year}."
            )

        # Rule 3: ISBN must be exactly 10 or 13 digits
        cleaned_isbn = self._clean_isbn(isbn)
        if not cleaned_isbn.isdigit() or len(cleaned_isbn) not in (10, 13):
            raise ValidationError(
                f"ISBN must be exactly 10 or 13 digits. Given: '{isbn}' ({len(cleaned_isbn)} digits)."
            )

        # Rule 4: Quantity cannot be negative
        if not isinstance(quantity, int) or quantity < 0:
            raise ValidationError("Quantity cannot be negative.")

        return cleaned_isbn

    # -----------------------------------------------------------------------
    # Use Case / Workflow Methods
    # -----------------------------------------------------------------------
    def add_book(
        self,
        title: str,
        author: str,
        isbn: str,
        publication_year: int,
        quantity: int = 1,
    ) -> Book:
        """Adds a new book after verifying business validation rules and ISBN uniqueness."""
        clean_isbn = self._validate_book_fields(
            title=title,
            author=author,
            isbn=isbn,
            publication_year=publication_year,
            quantity=quantity,
        )

        # Enforce unique ISBN in catalog
        existing = self.repository.get_by_isbn(clean_isbn)
        if existing:
            raise DuplicateISBNError(f"A book with ISBN '{isbn}' already exists in the collection.")

        new_book = Book(
            title=title.strip(),
            author=author.strip(),
            isbn=clean_isbn,
            publication_year=publication_year,
            quantity=quantity,
        )
        return self.repository.add(new_book)

    def get_all_books(self) -> List[Book]:
        """Retrieves all books in the collection."""
        return self.repository.get_all()

    def get_book_by_id(self, book_id: int) -> Book:
        """Retrieves a book by ID, raising BookNotFoundError if it does not exist."""
        book = self.repository.get_by_id(book_id)
        if not book:
            raise BookNotFoundError(f"Book with ID {book_id} was not found.")
        return book

    def search_books(self, query: str) -> List[Book]:
        """Searches books by title or author (partial match)."""
        clean_query = (query or "").strip()
        if not clean_query:
            return self.get_all_books()
        return self.repository.search(clean_query)

    def update_book(
        self,
        book_id: int,
        title: Optional[str] = None,
        author: Optional[str] = None,
        isbn: Optional[str] = None,
        publication_year: Optional[int] = None,
        quantity: Optional[int] = None,
    ) -> Book:
        """Updates any field of an existing book with domain rule validation."""
        book = self.get_book_by_id(book_id)

        target_title = title if title is not None else book.title
        target_author = author if author is not None else book.author
        target_isbn = isbn if isbn is not None else book.isbn
        target_year = publication_year if publication_year is not None else book.publication_year
        target_qty = quantity if quantity is not None else book.quantity

        clean_isbn = self._validate_book_fields(
            title=target_title,
            author=target_author,
            isbn=target_isbn,
            publication_year=target_year,
            quantity=target_qty,
        )

        # If ISBN is being changed, ensure it does not conflict with another book
        if clean_isbn != book.isbn:
            existing = self.repository.get_by_isbn(clean_isbn)
            if existing and existing.id != book.id:
                raise DuplicateISBNError(f"Another book already has ISBN '{clean_isbn}'.")

        book.title = target_title.strip()
        book.author = target_author.strip()
        book.isbn = clean_isbn
        book.publication_year = target_year
        book.quantity = target_qty

        return self.repository.update(book)

    def delete_book(self, book_id: int) -> None:
        """Deletes a book by ID. Raises BookNotFoundError if non-existent."""
        # Ensure book exists
        self.get_book_by_id(book_id)
        deleted = self.repository.delete(book_id)
        if not deleted:
            raise BookNotFoundError(f"Book with ID {book_id} could not be deleted.")

    def checkout_book(self, book_id: int) -> Book:
        """
        Checks out a book by decreasing its quantity by 1.
        Business Rule: A book cannot be checked out if quantity is already 0.
        Returns a meaningful OutOfStockError instead of crashing.
        """
        book = self.get_book_by_id(book_id)

        if book.quantity <= 0:
            raise OutOfStockError(
                f"Cannot check out '{book.title}'; quantity is already 0 (out of stock)."
            )

        book.quantity -= 1
        return self.repository.update(book)
