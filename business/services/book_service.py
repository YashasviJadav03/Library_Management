"""
Business Tier: Book Service.
Implements catalog business rules, validation, and domain policies.
"""
from typing import List, Optional
from data.models import Book
from data.repositories.book_repository import BookRepository
from data.repositories.borrow_repository import BorrowRepository
from business.exceptions import (
    BookNotFoundError,
    DuplicateISBNError,
    InvalidBookDataError,
    BookHasActiveLoansError,
)


class BookService:
    """Service handling business rules for catalog management."""

    def __init__(self, book_repo: BookRepository, borrow_repo: BorrowRepository):
        self.book_repo = book_repo
        self.borrow_repo = borrow_repo

    def add_book(
        self,
        title: str,
        author: str,
        isbn: str,
        category: str,
        total_copies: int = 1,
    ) -> Book:
        """
        Validates and adds a new book to the library catalog.
        Business Rules:
        - ISBN must be unique.
        - Total copies must be at least 1.
        - Initial available copies equals total copies.
        """
        clean_isbn = isbn.strip().replace("-", "")
        if not clean_isbn:
            raise InvalidBookDataError("ISBN cannot be empty.")
        if total_copies < 1:
            raise InvalidBookDataError("Total copies must be at least 1.")
        if not title.strip() or not author.strip() or not category.strip():
            raise InvalidBookDataError("Title, Author, and Category are required.")

        existing = self.book_repo.get_by_isbn(clean_isbn)
        if existing:
            raise DuplicateISBNError(f"A book with ISBN '{isbn}' already exists in the catalog.")

        book = Book(
            isbn=clean_isbn,
            title=title.strip(),
            author=author.strip(),
            category=category.strip(),
            total_copies=total_copies,
            available_copies=total_copies,
        )
        return self.book_repo.add(book)

    def get_book(self, book_id: int) -> Book:
        """Retrieves a book or raises BookNotFoundError."""
        book = self.book_repo.get_by_id(book_id)
        if not book:
            raise BookNotFoundError(f"Book with ID {book_id} does not exist.")
        return book

    def list_books(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Book]:
        """Lists books with search and pagination."""
        if limit < 1 or limit > 500:
            limit = 100
        if skip < 0:
            skip = 0
        return self.book_repo.list_books(search=search, category=category, skip=skip, limit=limit)

    def update_book(
        self,
        book_id: int,
        title: Optional[str] = None,
        author: Optional[str] = None,
        category: Optional[str] = None,
        total_copies: Optional[int] = None,
    ) -> Book:
        """
        Updates book attributes with business constraint enforcement.
        Business Rules:
        - Total copies cannot be reduced below the count of currently borrowed copies.
        """
        book = self.get_book(book_id)

        if title is not None:
            if not title.strip():
                raise InvalidBookDataError("Title cannot be empty.")
            book.title = title.strip()

        if author is not None:
            if not author.strip():
                raise InvalidBookDataError("Author cannot be empty.")
            book.author = author.strip()

        if category is not None:
            if not category.strip():
                raise InvalidBookDataError("Category cannot be empty.")
            book.category = category.strip()

        if total_copies is not None:
            if total_copies < 1:
                raise InvalidBookDataError("Total copies must be at least 1.")
            currently_borrowed = book.total_copies - book.available_copies
            if total_copies < currently_borrowed:
                raise InvalidBookDataError(
                    f"Cannot reduce total copies to {total_copies}; "
                    f"{currently_borrowed} copies are currently loaned out."
                )
            # Adjust available copies proportionally
            book.available_copies = total_copies - currently_borrowed
            book.total_copies = total_copies

        return self.book_repo.update(book)

    def delete_book(self, book_id: int) -> None:
        """
        Removes a book from catalog.
        Business Rule:
        - Book cannot be deleted if any copies are currently loaned out.
        """
        book = self.get_book(book_id)
        active_loans = self.borrow_repo.get_active_borrows_by_book(book_id)
        if active_loans or (book.available_copies < book.total_copies):
            raise BookHasActiveLoansError(
                f"Cannot delete book '{book.title}'; there are currently active loans."
            )
        self.book_repo.delete(book)
