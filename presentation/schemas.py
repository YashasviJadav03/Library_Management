"""
Presentation Tier: Request and Response DTO Schemas.
Handles input deserialization and response serialization.
Does NOT enforce domain business rules (that is delegated to Business Tier).
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class BookCreate(BaseModel):
    title: str
    author: str
    isbn: str
    publication_year: int
    quantity: int = 1


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    publication_year: Optional[int] = None
    quantity: Optional[int] = None


class BookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str
    isbn: str
    publication_year: int
    quantity: int
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    message: str
