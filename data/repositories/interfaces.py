"""
Data Tier: Repository Interfaces.
Defines the abstract contract for data access.
Enables pluggable data layers (e.g. SQLite, in-memory list)
so the Business Logic tier remains completely decoupled from database specifics.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from data.models import Book


class IBookRepository(ABC):
    """Abstract interface for Book data access operations."""

    @abstractmethod
    def add(self, book: Book) -> Book:
        """Add a new book entity to storage."""
        pass

    @abstractmethod
    def get_by_id(self, book_id: int) -> Optional[Book]:
        """Fetch a book by its primary ID."""
        pass

    @abstractmethod
    def get_by_isbn(self, isbn: str) -> Optional[Book]:
        """Fetch a book by its ISBN."""
        pass

    @abstractmethod
    def get_all(self) -> List[Book]:
        """Return all books in storage."""
        pass

    @abstractmethod
    def search(self, query: str) -> List[Book]:
        """Search books by title or author (case-insensitive partial match)."""
        pass

    @abstractmethod
    def update(self, book: Book) -> Book:
        """Update an existing book entity."""
        pass

    @abstractmethod
    def delete(self, book_id: int) -> bool:
        """Delete a book by ID. Returns True if deleted, False if not found."""
        pass
