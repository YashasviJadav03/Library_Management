"""
Presentation Tier: Pydantic DTO Schemas.
Handles request validation and response serialisation.
"""
import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from data.models import MembershipType, BorrowStatus

EMAIL_PATTERN = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")


# ---------------------------------------------------------------------------
# Book Schemas
# ---------------------------------------------------------------------------
class BookCreate(BaseModel):
    isbn: str = Field(..., json_schema_extra={"example": "978-0132350884"}, description="Unique ISBN code")
    title: str = Field(..., min_length=1, max_length=255, json_schema_extra={"example": "Clean Code"})
    author: str = Field(..., min_length=1, max_length=255, json_schema_extra={"example": "Robert C. Martin"})
    category: str = Field(..., min_length=1, max_length=100, json_schema_extra={"example": "Software Engineering"})
    total_copies: int = Field(default=1, ge=1, json_schema_extra={"example": 5}, description="Number of copies acquired")


class BookUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    author: Optional[str] = Field(default=None, min_length=1, max_length=255)
    category: Optional[str] = Field(default=None, min_length=1, max_length=100)
    total_copies: Optional[int] = Field(default=None, ge=1)


class BookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    isbn: str
    title: str
    author: str
    category: str
    total_copies: int
    available_copies: int
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Member Schemas
# ---------------------------------------------------------------------------
class MemberCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, json_schema_extra={"example": "Alice Johnson"})
    email: str = Field(..., json_schema_extra={"example": "alice@university.edu"})
    membership_type: MembershipType = Field(default=MembershipType.STUDENT, json_schema_extra={"example": MembershipType.STUDENT})
    custom_limit: Optional[int] = Field(default=None, ge=1, json_schema_extra={"example": 3})

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_PATTERN.match(v):
            raise ValueError(f"Invalid email address format: '{v}'")
        return v


class MemberUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    membership_type: Optional[MembershipType] = None
    max_borrow_limit: Optional[int] = Field(default=None, ge=1)
    is_active: Optional[bool] = None


class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    membership_type: MembershipType
    max_borrow_limit: int
    is_active: bool
    created_at: datetime


# ---------------------------------------------------------------------------
# Borrow / Return Schemas
# ---------------------------------------------------------------------------
class BorrowRequest(BaseModel):
    member_id: int = Field(..., json_schema_extra={"example": 1})
    book_id: int = Field(..., json_schema_extra={"example": 1})
    loan_days: int = Field(default=14, ge=1, le=90, json_schema_extra={"example": 14})


class ReturnRequest(BaseModel):
    return_time: Optional[datetime] = None


class BorrowRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    member_id: int
    borrow_date: datetime
    due_date: datetime
    return_date: Optional[datetime] = None
    fine_amount: float
    status: BorrowStatus


class MessageResponse(BaseModel):
    message: str
