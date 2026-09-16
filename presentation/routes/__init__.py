"""Presentation API Routes Package."""
from presentation.routes.book_routes import router as books_router
from presentation.routes.member_routes import router as members_router
from presentation.routes.borrow_routes import router as borrow_router

__all__ = ["books_router", "members_router", "borrow_router"]
