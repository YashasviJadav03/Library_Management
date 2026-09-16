"""Data Repositories package."""
from data.repositories.interfaces import IBookRepository
from data.repositories.book_repository import BookRepository
from data.repositories.memory_repository import InMemoryBookRepository

__all__ = ["IBookRepository", "BookRepository", "InMemoryBookRepository"]
