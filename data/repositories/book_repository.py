"""
Data Tier: Book Repository.
Encapsulates all database operations and SQL queries for Books.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from data.models import Book


class BookRepository:
    """Repository handling database operations for Book entities."""

    def __init__(self, db: Session):
        self.db = db

    def add(self, book: Book) -> Book:
        """Persists a new book to the database."""
        self.db.add(book)
        self.db.commit()
        self.db.refresh(book)
        return book

    def get_by_id(self, book_id: int) -> Optional[Book]:
        """Retrieves a book by its primary key ID."""
        return self.db.query(Book).filter(Book.id == book_id).first()

    def get_by_isbn(self, isbn: str) -> Optional[Book]:
        """Retrieves a book by its unique ISBN."""
        return self.db.query(Book).filter(Book.isbn == isbn).first()

    def list_books(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Book]:
        """Retrieves a paginated list of books with optional search filtering."""
        query = self.db.query(Book)
        if category:
            query = query.filter(Book.category.ilike(f"%{category}%"))
        if search:
            search_filter = or_(
                Book.title.ilike(f"%{search}%"),
                Book.author.ilike(f"%{search}%"),
                Book.isbn.ilike(f"%{search}%"),
            )
            query = query.filter(search_filter)
        return query.offset(skip).limit(limit).all()

    def update(self, book: Book) -> Book:
        """Commits updates to an existing book."""
        self.db.commit()
        self.db.refresh(book)
        return book

    def delete(self, book: Book) -> None:
        """Deletes a book entity from the database."""
        self.db.delete(book)
        self.db.commit()
