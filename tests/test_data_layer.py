"""
Unit Tests for Data Tier: Repositories and ORM Entities.
Verifies CRUD and query logic isolated from higher layers.
"""
from datetime import datetime, timedelta
from data.models import Book, Member, BorrowRecord, MembershipType, BorrowStatus
from data.repositories.book_repository import BookRepository
from data.repositories.member_repository import MemberRepository
from data.repositories.borrow_repository import BorrowRepository


class TestBookRepository:
    def test_add_and_get_book(self, db_session):
        repo = BookRepository(db_session)
        book = Book(
            isbn="1234567890",
            title="Design Patterns",
            author="Gang of Four",
            category="CS",
            total_copies=2,
            available_copies=2,
        )
        saved = repo.add(book)
        assert saved.id is not None
        assert repo.get_by_id(saved.id).title == "Design Patterns"
        assert repo.get_by_isbn("1234567890") is not None

    def test_list_books_search(self, db_session):
        repo = BookRepository(db_session)
        repo.add(Book(isbn="111", title="Python 101", author="Guido", category="Tech", total_copies=1, available_copies=1))
        repo.add(Book(isbn="222", title="Cooking Basics", author="Chef", category="Culinary", total_copies=1, available_copies=1))

        tech_books = repo.list_books(category="Tech")
        assert len(tech_books) == 1
        assert tech_books[0].title == "Python 101"

        search_results = repo.list_books(search="python")
        assert len(search_results) == 1

    def test_delete_book(self, db_session):
        repo = BookRepository(db_session)
        book = repo.add(Book(isbn="333", title="Temp", author="A", category="C", total_copies=1, available_copies=1))
        book_id = book.id
        repo.delete(book)
        assert repo.get_by_id(book_id) is None


class TestMemberRepository:
    def test_add_and_get_member(self, db_session):
        repo = MemberRepository(db_session)
        member = Member(
            name="Bob Smith",
            email="bob@example.com",
            membership_type=MembershipType.FACULTY,
            max_borrow_limit=10,
            is_active=True,
        )
        saved = repo.add(member)
        assert saved.id is not None
        assert repo.get_by_email("bob@example.com") is not None

    def test_update_member(self, db_session):
        repo = MemberRepository(db_session)
        member = repo.add(Member(name="Test", email="t@ex.com", max_borrow_limit=3, is_active=True))
        member.is_active = False
        updated = repo.update(member)
        assert updated.is_active is False


class TestBorrowRepository:
    def test_borrow_record_lifecycle(self, db_session, sample_book, sample_member):
        repo = BorrowRepository(db_session)
        now = datetime.utcnow()
        due = now + timedelta(days=14)

        record = BorrowRecord(
            book_id=sample_book.id,
            member_id=sample_member.id,
            borrow_date=now,
            due_date=due,
            status=BorrowStatus.BORROWED,
        )
        saved = repo.add(record)
        assert saved.id is not None
        assert saved.status == BorrowStatus.BORROWED

        active = repo.get_active_borrows_by_member(sample_member.id)
        assert len(active) == 1

        # Mark returned
        saved.status = BorrowStatus.RETURNED
        saved.return_date = datetime.utcnow()
        repo.update(saved)

        assert len(repo.get_active_borrows_by_member(sample_member.id)) == 0
