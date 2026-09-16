"""
Pytest configuration and shared fixtures for unit and integration testing.
Uses an in-memory SQLite database isolated per test.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from data.database import Base, get_db
from data.models import Book, Member, MembershipType
from presentation.main import app

# In-memory SQLite database with StaticPool so all connections share the same memory DB
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Provides a fresh database session with newly created tables for each test."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden DB dependency pointing to in-memory database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_book(db_session):
    """Creates and returns a sample book entity."""
    book = Book(
        isbn="9780132350884",
        title="Clean Code",
        author="Robert C. Martin",
        category="Software Engineering",
        total_copies=3,
        available_copies=3,
    )
    db_session.add(book)
    db_session.commit()
    db_session.refresh(book)
    return book


@pytest.fixture
def sample_member(db_session):
    """Creates and returns a sample student member entity."""
    member = Member(
        name="John Doe",
        email="john.doe@example.com",
        membership_type=MembershipType.STUDENT,
        max_borrow_limit=3,
        is_active=True,
    )
    db_session.add(member)
    db_session.commit()
    db_session.refresh(member)
    return member
