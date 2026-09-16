"""
Business Tier: Custom Domain Exceptions.
Clean, framework-agnostic domain exceptions representing business rule violations.
"""

class LibraryDomainException(Exception):
    """Base exception for all domain-level business errors."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class BookNotFoundError(LibraryDomainException):
    """Raised when a requested book is not found in the catalog."""
    pass


class DuplicateISBNError(LibraryDomainException):
    """Raised when attempting to add a book with an ISBN that already exists."""
    pass


class InvalidBookDataError(LibraryDomainException):
    """Raised when book data violates domain constraints."""
    pass


class BookNotAvailableError(LibraryDomainException):
    """Raised when attempting to borrow a book with 0 available copies."""
    pass


class BookHasActiveLoansError(LibraryDomainException):
    """Raised when attempting to delete a book that is currently loaned out."""
    pass


class MemberNotFoundError(LibraryDomainException):
    """Raised when a requested member does not exist."""
    pass


class DuplicateEmailError(LibraryDomainException):
    """Raised when attempting to register a member with an existing email."""
    pass


class MemberInactiveError(LibraryDomainException):
    """Raised when an inactive member attempts to borrow materials."""
    pass


class BorrowLimitExceededError(LibraryDomainException):
    """Raised when a member has reached or exceeded their maximum checkout limit."""
    pass


class BorrowRecordNotFoundError(LibraryDomainException):
    """Raised when a borrow/return record is not found."""
    pass


class BookAlreadyReturnedError(LibraryDomainException):
    """Raised when attempting to return a book that has already been returned."""
    pass
