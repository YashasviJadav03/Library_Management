"""
Presentation Tier: Borrowing & Returns Routes.
Exposes RESTful endpoints for checkouts, returns, loan history, and fine assessments.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from data.database import get_db
from data.models import BorrowStatus
from data.repositories.book_repository import BookRepository
from data.repositories.member_repository import MemberRepository
from data.repositories.borrow_repository import BorrowRepository
from business.services.borrow_service import BorrowService
from presentation.schemas import (
    BorrowRequest,
    ReturnRequest,
    BorrowRecordResponse,
)

router = APIRouter(prefix="/borrow", tags=["Borrowing & Returns"])


def get_borrow_service(db: Session = Depends(get_db)) -> BorrowService:
    """Dependency injection helper for BorrowService."""
    return BorrowService(
        book_repo=BookRepository(db),
        member_repo=MemberRepository(db),
        borrow_repo=BorrowRepository(db),
    )


@router.post("/", response_model=BorrowRecordResponse, status_code=status.HTTP_201_CREATED)
def checkout_book(
    payload: BorrowRequest,
    service: BorrowService = Depends(get_borrow_service),
):
    """
    Borrow a book for a library member.
    Enforces borrowing limit, active membership, and copy availability.
    """
    return service.borrow_book(
        member_id=payload.member_id,
        book_id=payload.book_id,
        loan_days=payload.loan_days,
    )


@router.post("/return/{record_id}", response_model=BorrowRecordResponse)
def return_book(
    record_id: int,
    payload: Optional[ReturnRequest] = None,
    service: BorrowService = Depends(get_borrow_service),
):
    """
    Return a borrowed book.
    Restores available copy count and automatically calculates overdue fines.
    """
    return_time = payload.return_time if payload else None
    return service.return_book(record_id=record_id, return_time=return_time)


@router.get("/records", response_model=List[BorrowRecordResponse])
def list_borrow_records(
    member_id: Optional[int] = Query(None, description="Filter by member ID"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    status: Optional[BorrowStatus] = Query(None, description="Filter by status (BORROWED or RETURNED)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: BorrowService = Depends(get_borrow_service),
):
    """View all borrowing transaction records with optional filters."""
    return service.list_records(
        member_id=member_id,
        book_id=book_id,
        status=status,
        skip=skip,
        limit=limit,
    )


@router.get("/records/{record_id}", response_model=BorrowRecordResponse)
def get_borrow_record(
    record_id: int,
    service: BorrowService = Depends(get_borrow_service),
):
    """Retrieve details of a specific borrowing transaction."""
    return service.get_record(record_id)
