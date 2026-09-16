"""
Presentation Tier: Book REST API Routes.
Handles HTTP requests, parameter parsing, and maps domain exceptions to HTTP status codes.
Never calls the database directly — delegates exclusively to BookService.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from data.database import get_db
from data.repositories.book_repository import BookRepository
from business.book_service import BookService
from presentation.schemas import BookCreate, BookUpdate, BookResponse, MessageResponse

router = APIRouter(prefix="/books", tags=["Books"])


def get_book_service(db: Session = Depends(get_db)) -> BookService:
    """Dependency injection helper: injects concrete SQLite repository into BookService."""
    repository = BookRepository(db)
    return BookService(repository=repository)


@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def add_book(
    payload: BookCreate,
    service: BookService = Depends(get_book_service),
):
    """Add a new book to the collection."""
    return service.add_book(
        title=payload.title,
        author=payload.author,
        isbn=payload.isbn,
        publication_year=payload.publication_year,
        quantity=payload.quantity,
    )


@router.get("/", response_model=List[BookResponse])
def get_books(
    query: Optional[str] = Query(None, description="Search by title or author (partial match)"),
    service: BookService = Depends(get_book_service),
):
    """View all books or search by title/author."""
    if query:
        return service.search_books(query)
    return service.get_all_books()


@router.get("/{book_id}", response_model=BookResponse)
def get_book(
    book_id: int,
    service: BookService = Depends(get_book_service),
):
    """View details of a single book by ID."""
    return service.get_book_by_id(book_id)


@router.put("/{book_id}", response_model=BookResponse)
def update_book(
    book_id: int,
    payload: BookUpdate,
    service: BookService = Depends(get_book_service),
):
    """Edit any field of an existing book."""
    return service.update_book(
        book_id=book_id,
        title=payload.title,
        author=payload.author,
        isbn=payload.isbn,
        publication_year=payload.publication_year,
        quantity=payload.quantity,
    )


@router.delete("/{book_id}", response_model=MessageResponse)
def delete_book(
    book_id: int,
    service: BookService = Depends(get_book_service),
):
    """Remove a book by ID."""
    service.delete_book(book_id)
    return MessageResponse(message=f"Book with ID {book_id} successfully deleted.")


@router.post("/{book_id}/checkout", response_model=BookResponse)
def checkout_book(
    book_id: int,
    service: BookService = Depends(get_book_service),
):
    """Check out a book (decrease quantity by 1)."""
    return service.checkout_book(book_id)
