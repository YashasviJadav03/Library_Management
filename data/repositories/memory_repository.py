"""
Data Tier: In-Memory List Implementation.
Second implementation of IBookRepository using a pure Python in-memory list/dict.
Used for unit testing without a database and for the data layer swap demonstration.
"""
from datetime import datetime
from typing import List, Optional, Dict
from data.models import Book
from data.repositories.interfaces import IBookRepository


class InMemoryBookRepository(IBookRepository):
    """In-memory data store for books using a Python dictionary/list."""

    def __init__(self):
        self.books: Dict[int, Book] = {}
        self._next_id: int = 1

    def add(self, book: Book) -> Book:
        if getattr(book, "id", None) is None:
            book.id = self._next_id
            self._next_id += 1
        book.created_at = getattr(book, "created_at", None) or datetime.utcnow()
        book.updated_at = datetime.utcnow()
        self.books[book.id] = book
        return book

    def get_by_id(self, book_id: int) -> Optional[Book]:
        return self.books.get(book_id)

    def get_by_isbn(self, isbn: str) -> Optional[Book]:
        clean_isbn = isbn.replace("-", "").strip()
        for book in self.books.values():
            if book.isbn.replace("-", "").strip() == clean_isbn:
                return book
        return None

    def get_all(self) -> List[Book]:
        return list(self.books.values())

    def search(self, query: str) -> List[Book]:
        q = query.lower().strip()
        return [
            b for b in self.books.values()
            if q in b.title.lower() or q in b.author.lower()
        ]

    def update(self, book: Book) -> Book:
        book.updated_at = datetime.utcnow()
        self.books[book.id] = book
        return book

    def delete(self, book_id: int) -> bool:
        if book_id in self.books:
            del self.books[book_id]
            return True
        return False
