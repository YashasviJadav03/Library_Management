"""
Presentation Tier: Member Routes.
Exposes RESTful endpoints for library card holders and membership.
"""
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from data.database import get_db
from data.repositories.member_repository import MemberRepository
from data.repositories.borrow_repository import BorrowRepository
from business.services.member_service import MemberService
from business.services.borrow_service import BorrowService
from presentation.schemas import (
    MemberCreate,
    MemberUpdate,
    MemberResponse,
    BorrowRecordResponse,
    MessageResponse,
)

router = APIRouter(prefix="/members", tags=["Members"])


def get_member_service(db: Session = Depends(get_db)) -> MemberService:
    """Dependency injection helper for MemberService."""
    member_repo = MemberRepository(db)
    borrow_repo = BorrowRepository(db)
    return MemberService(member_repo=member_repo, borrow_repo=borrow_repo)


def get_borrow_service(db: Session = Depends(get_db)) -> BorrowService:
    """Dependency injection helper for BorrowService."""
    from data.repositories.book_repository import BookRepository
    return BorrowService(
        book_repo=BookRepository(db),
        member_repo=MemberRepository(db),
        borrow_repo=BorrowRepository(db),
    )


@router.post("/", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
def register_member(
    payload: MemberCreate,
    service: MemberService = Depends(get_member_service),
):
    """Register a new library member."""
    return service.register_member(
        name=payload.name,
        email=payload.email,
        membership_type=payload.membership_type,
        custom_limit=payload.custom_limit,
    )


@router.get("/", response_model=List[MemberResponse])
def list_members(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    active_only: bool = Query(False, description="Filter for active members only"),
    service: MemberService = Depends(get_member_service),
):
    """Retrieve list of library members."""
    return service.list_members(skip=skip, limit=limit, active_only=active_only)


@router.get("/{member_id}", response_model=MemberResponse)
def get_member(
    member_id: int,
    service: MemberService = Depends(get_member_service),
):
    """Retrieve details for a specific member."""
    return service.get_member(member_id)


@router.put("/{member_id}", response_model=MemberResponse)
def update_member(
    member_id: int,
    payload: MemberUpdate,
    service: MemberService = Depends(get_member_service),
):
    """Update member profile details."""
    return service.update_member(
        member_id=member_id,
        name=payload.name,
        membership_type=payload.membership_type,
        max_borrow_limit=payload.max_borrow_limit,
        is_active=payload.is_active,
    )


@router.delete("/{member_id}", response_model=MessageResponse)
def delete_member(
    member_id: int,
    service: MemberService = Depends(get_member_service),
):
    """Delete a member record (forbidden if unreturned loans exist)."""
    service.delete_member(member_id)
    return MessageResponse(message=f"Member with ID {member_id} successfully deleted.")


@router.get("/{member_id}/active-loans", response_model=List[BorrowRecordResponse])
def get_member_active_loans(
    member_id: int,
    service: BorrowService = Depends(get_borrow_service),
):
    """Get list of active book loans for a specific member."""
    return service.get_member_active_borrows(member_id)
