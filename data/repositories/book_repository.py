"""
Data Tier: SQLite / SQLAlchemy Book Repository.
Concrete implementation of IBookRepository using SQLAlchemy and SQLite.
Contains only data persistence logic — no validation or display logic.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from data.models import Book
from data.repositories.interfaces import IBookRepository


class BookRepository(IBookRepository):
    """SQLite data layer implementation for books."""

    def __init__(self, db: Session):
        self.db = db

    def add(self, book: Book) -> Book:
        self.db.add(book)
        self.db.commit()
        self.db.refresh(book)
        return book

    def get_by_id(self, book_id: int) -> Optional[Book]:
        return self.db.query(Book).filter(Book.id == book_id).first()

    def get_by_isbn(self, isbn: str) -> Optional[Book]:
        return self.db.query(Book).filter(Book.isbn == isbn).first()

    def get_all(self) -> List[Book]:
        return self.db.query(Book).order_by(Book.id.asc()).all()

    def search(self, query: str) -> List[Book]:
        pattern = f"%{query}%"
        return (
            self.db.query(Book)
            .filter(
                or_(
                    Book.title.ilike(pattern),
                    Book.author.ilike(pattern),
                )
            )
            .order_by(Book.id.asc())
            .all()
        )

    def update(self, book: Book) -> Book:
        self.db.commit()
        self.db.refresh(book)
        return book

    def delete(self, book_id: int) -> bool:
        book = self.get_by_id(book_id)
        if not book:
            return False
        self.db.delete(book)
        self.db.commit()
        return True
