"""
Presentation Tier: Main Application.
FastAPI app configuration, middleware, exception mapping, and router registration.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from data.database import init_db
from presentation.routes.book_routes import router as books_router
from presentation.routes.member_routes import router as members_router
from presentation.routes.borrow_routes import router as borrow_router
from business.exceptions import (
    LibraryDomainException,
    BookNotFoundError,
    MemberNotFoundError,
    BorrowRecordNotFoundError,
    DuplicateISBNError,
    DuplicateEmailError,
    BookNotAvailableError,
    BorrowLimitExceededError,
    MemberInactiveError,
    BookHasActiveLoansError,
    BookAlreadyReturnedError,
    InvalidBookDataError,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise database tables upon application startup."""
    init_db()
    yield


app = FastAPI(
    title="Library Management System API",
    description=(
        "A 3-Tier Architecture Library Management System implemented in Python FastAPI. "
        "Separated cleanly into Presentation, Business, and Data tiers."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Global Exception Handlers: Map Business Tier Exceptions to HTTP Status Codes
# ---------------------------------------------------------------------------
@app.exception_handler(BookNotFoundError)
@app.exception_handler(MemberNotFoundError)
@app.exception_handler(BorrowRecordNotFoundError)
async def not_found_handler(request: Request, exc: LibraryDomainException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": "Not Found", "detail": exc.message},
    )


@app.exception_handler(DuplicateISBNError)
@app.exception_handler(DuplicateEmailError)
async def conflict_handler(request: Request, exc: LibraryDomainException):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"error": "Conflict", "detail": exc.message},
    )


@app.exception_handler(BookNotAvailableError)
@app.exception_handler(BorrowLimitExceededError)
@app.exception_handler(MemberInactiveError)
@app.exception_handler(BookHasActiveLoansError)
@app.exception_handler(BookAlreadyReturnedError)
@app.exception_handler(InvalidBookDataError)
async def bad_request_handler(request: Request, exc: LibraryDomainException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Bad Request", "detail": exc.message},
    )


# Register Routers under /api
app.include_router(books_router, prefix="/api")
app.include_router(members_router, prefix="/api")
app.include_router(borrow_router, prefix="/api")


@app.get("/", tags=["System"])
def root():
    """System welcome and info endpoint."""
    return {
        "message": "Welcome to the 3-Tier Library Management System API",
        "architecture": "3-Tier (Presentation, Business, Data)",
        "documentation": "/docs",
        "health": "/health",
        "version": "1.0.0",
    }


@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy"}
