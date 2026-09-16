"""
Pytest configuration and shared fixtures for unit and integration testing.
Uses an in-memory SQLite database with StaticPool so all test connections share tables.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from data.database import Base, get_db
from data.models import Book
from presentation.main import app

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Provides a fresh isolated database session with created tables."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden DB dependency."""
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
    """Creates a sample book entity in the test database."""
    book = Book(
        title="Clean Code",
        author="Robert C. Martin",
        isbn="9780132350884",
        publication_year=2008,
        quantity=3,
    )
    db_session.add(book)
    db_session.commit()
    db_session.refresh(book)
    return book
