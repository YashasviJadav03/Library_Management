"""
Presentation Tier: Book Routes.
Exposes RESTful endpoints for catalog management.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from data.database import get_db
from data.repositories.book_repository import BookRepository
from data.repositories.borrow_repository import BorrowRepository
from business.services.book_service import BookService
from presentation.schemas import BookCreate, BookUpdate, BookResponse, MessageResponse

router = APIRouter(prefix="/books", tags=["Books"])


def get_book_service(db: Session = Depends(get_db)) -> BookService:
    """Dependency injection helper for BookService."""
    book_repo = BookRepository(db)
    borrow_repo = BorrowRepository(db)
    return BookService(book_repo=book_repo, borrow_repo=borrow_repo)


@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(
    payload: BookCreate,
    service: BookService = Depends(get_book_service),
):
    """Add a new book to the library catalog."""
    return service.add_book(
        title=payload.title,
        author=payload.author,
        isbn=payload.isbn,
        category=payload.category,
        total_copies=payload.total_copies,
    )


@router.get("/", response_model=List[BookResponse])
def list_books(
    search: Optional[str] = Query(None, description="Search keyword matching title, author, or ISBN"),
    category: Optional[str] = Query(None, description="Filter by genre or category"),
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Page limit"),
    service: BookService = Depends(get_book_service),
):
    """Retrieve catalog books with optional keyword search and category filters."""
    return service.list_books(search=search, category=category, skip=skip, limit=limit)


@router.get("/{book_id}", response_model=BookResponse)
def get_book(
    book_id: int,
    service: BookService = Depends(get_book_service),
):
    """Retrieve details for a specific book by ID."""
    return service.get_book(book_id)


@router.put("/{book_id}", response_model=BookResponse)
def update_book(
    book_id: int,
    payload: BookUpdate,
    service: BookService = Depends(get_book_service),
):
    """Update book details and copy counts under business validation."""
    return service.update_book(
        book_id=book_id,
        title=payload.title,
        author=payload.author,
        category=payload.category,
        total_copies=payload.total_copies,
    )


@router.delete("/{book_id}", response_model=MessageResponse)
def delete_book(
    book_id: int,
    service: BookService = Depends(get_book_service),
):
    """Remove a book from catalog (only if no active loans exist)."""
    service.delete_book(book_id)
    return MessageResponse(message=f"Book with ID {book_id} successfully deleted.")
