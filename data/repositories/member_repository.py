"""
Data Tier: Member Repository.
Encapsulates all database operations and SQL queries for Members.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from data.models import Member


class MemberRepository:
    """Repository handling database operations for Member entities."""

    def __init__(self, db: Session):
        self.db = db

    def add(self, member: Member) -> Member:
        """Persists a new member to the database."""
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

    def get_by_id(self, member_id: int) -> Optional[Member]:
        """Retrieves a member by their primary key ID."""
        return self.db.query(Member).filter(Member.id == member_id).first()

    def get_by_email(self, email: str) -> Optional[Member]:
        """Retrieves a member by their unique email."""
        return self.db.query(Member).filter(Member.email == email).first()

    def list_members(self, skip: int = 0, limit: int = 100, active_only: bool = False) -> List[Member]:
        """Retrieves a paginated list of members."""
        query = self.db.query(Member)
        if active_only:
            query = query.filter(Member.is_active == True)
        return query.offset(skip).limit(limit).all()

    def update(self, member: Member) -> Member:
        """Commits updates to an existing member."""
        self.db.commit()
        self.db.refresh(member)
        return member

    def delete(self, member: Member) -> None:
        """Deletes a member entity from the database."""
        self.db.delete(member)
        self.db.commit()
