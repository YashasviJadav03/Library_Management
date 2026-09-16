"""
Unit Tests for Data Tier: BookRepository (SQLite / SQLAlchemy).
Verifies CRUD queries and persistence logic isolated from the business tier.
"""
from data.models import Book
from data.repositories.book_repository import BookRepository


class TestBookRepository:
    def test_add_and_get_book(self, db_session):
        repo = BookRepository(db_session)
        book = Book(
            title="Design Patterns",
            author="Erich Gamma",
            isbn="9780201633610",
            publication_year=1994,
            quantity=2,
        )
        saved = repo.add(book)
        assert saved.id is not None
        assert repo.get_by_id(saved.id).title == "Design Patterns"
        assert repo.get_by_isbn("9780201633610") is not None

    def test_search_books_by_title_and_author(self, db_session):
        repo = BookRepository(db_session)
        repo.add(Book(title="Python Crash Course", author="Eric Matthes", isbn="9781593279288", publication_year=2019, quantity=5))
        repo.add(Book(title="Fluent Python", author="Luciano Ramalho", isbn="9781491946008", publication_year=2015, quantity=3))
        repo.add(Book(title="The Pragmatic Programmer", author="David Thomas", isbn="9780135957059", publication_year=2019, quantity=2))

        # Search by partial title
        res = repo.search("python")
        assert len(res) == 2

        # Search by author
        res2 = repo.search("ramalho")
        assert len(res2) == 1
        assert res2[0].title == "Fluent Python"

    def test_update_book(self, db_session, sample_book):
        repo = BookRepository(db_session)
        sample_book.quantity = 10
        updated = repo.update(sample_book)
        assert updated.quantity == 10
        assert repo.get_by_id(sample_book.id).quantity == 10

    def test_delete_book(self, db_session, sample_book):
        repo = BookRepository(db_session)
        book_id = sample_book.id
        deleted = repo.delete(book_id)
        assert deleted is True
        assert repo.get_by_id(book_id) is None

        # Deleting again returns False
        assert repo.delete(book_id) is False
