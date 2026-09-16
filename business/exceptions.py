"""
Business Tier: Custom Domain Exceptions.
These exceptions represent business rule and validation failures.
They are completely decoupled from HTTP frameworks (no HTTPException here)
and decoupled from database engines.
"""

class BusinessRuleException(Exception):
    """Base exception for all business logic and validation violations."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ValidationError(BusinessRuleException):
    """Raised when book data violates domain validation rules."""
    pass


class BookNotFoundError(BusinessRuleException):
    """Raised when a book with the given ID does not exist."""
    pass


class OutOfStockError(BusinessRuleException):
    """Raised when checking out a book whose quantity is already 0."""
    pass


class DuplicateISBNError(BusinessRuleException):
    """Raised when adding a book with an ISBN that already exists."""
    pass
