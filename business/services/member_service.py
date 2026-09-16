"""
Business Tier: Member Service.
Implements membership business rules, validation, and loan limits.
"""
import re
from typing import List, Optional
from data.models import Member, MembershipType
from data.repositories.member_repository import MemberRepository
from data.repositories.borrow_repository import BorrowRepository
from business.exceptions import (
    MemberNotFoundError,
    DuplicateEmailError,
    InvalidBookDataError,
    BookHasActiveLoansError,
)

DEFAULT_BORROW_LIMITS = {
    MembershipType.STUDENT: 3,
    MembershipType.FACULTY: 10,
    MembershipType.GENERAL: 2,
}

EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")


class MemberService:
    """Service handling business rules for library membership."""

    def __init__(self, member_repo: MemberRepository, borrow_repo: BorrowRepository):
        self.member_repo = member_repo
        self.borrow_repo = borrow_repo

    def register_member(
        self,
        name: str,
        email: str,
        membership_type: MembershipType = MembershipType.STUDENT,
        custom_limit: Optional[int] = None,
    ) -> Member:
        """
        Validates and registers a new library member.
        Business Rules:
        - Name cannot be empty.
        - Valid email format.
        - Email must be unique.
        - Max borrow limit defaults according to membership tier unless specified.
        """
        clean_name = name.strip()
        clean_email = email.strip().lower()

        if not clean_name:
            raise InvalidBookDataError("Member name cannot be empty.")
        if not EMAIL_REGEX.match(clean_email):
            raise InvalidBookDataError(f"Invalid email format: '{email}'.")

        existing = self.member_repo.get_by_email(clean_email)
        if existing:
            raise DuplicateEmailError(f"A member with email '{clean_email}' already exists.")

        limit = custom_limit if custom_limit is not None else DEFAULT_BORROW_LIMITS.get(membership_type, 3)
        if limit < 1:
            raise InvalidBookDataError("Borrow limit must be at least 1.")

        member = Member(
            name=clean_name,
            email=clean_email,
            membership_type=membership_type,
            max_borrow_limit=limit,
            is_active=True,
        )
        return self.member_repo.add(member)

    def get_member(self, member_id: int) -> Member:
        """Retrieves a member or raises MemberNotFoundError."""
        member = self.member_repo.get_by_id(member_id)
        if not member:
            raise MemberNotFoundError(f"Member with ID {member_id} does not exist.")
        return member

    def list_members(self, skip: int = 0, limit: int = 100, active_only: bool = False) -> List[Member]:
        """Lists members with pagination."""
        if limit < 1 or limit > 500:
            limit = 100
        if skip < 0:
            skip = 0
        return self.member_repo.list_members(skip=skip, limit=limit, active_only=active_only)

    def update_member(
        self,
        member_id: int,
        name: Optional[str] = None,
        membership_type: Optional[MembershipType] = None,
        max_borrow_limit: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> Member:
        """Updates member profile attributes."""
        member = self.get_member(member_id)

        if name is not None:
            if not name.strip():
                raise InvalidBookDataError("Member name cannot be empty.")
            member.name = name.strip()

        if membership_type is not None:
            member.membership_type = membership_type
            if max_borrow_limit is None:
                member.max_borrow_limit = DEFAULT_BORROW_LIMITS.get(membership_type, member.max_borrow_limit)

        if max_borrow_limit is not None:
            if max_borrow_limit < 1:
                raise InvalidBookDataError("Borrow limit must be at least 1.")
            member.max_borrow_limit = max_borrow_limit

        if is_active is not None:
            if is_active is False:
                # Check for active loans
                active_loans = self.borrow_repo.get_active_borrows_by_member(member_id)
                if active_loans:
                    raise BookHasActiveLoansError(
                        f"Cannot deactivate member {member.name}; {len(active_loans)} books are currently borrowed."
                    )
            member.is_active = is_active

        return self.member_repo.update(member)

    def delete_member(self, member_id: int) -> None:
        """
        Deletes a member.
        Business Rule:
        - Cannot delete a member with active borrowed items.
        """
        member = self.get_member(member_id)
        active_loans = self.borrow_repo.get_active_borrows_by_member(member_id)
        if active_loans:
            raise BookHasActiveLoansError(
                f"Cannot delete member '{member.name}'; {len(active_loans)} active loans must be returned first."
            )
        self.member_repo.delete(member)
