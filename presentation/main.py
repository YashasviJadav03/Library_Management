"""
Presentation Tier: Main FastAPI Application.
Coordinates routes, global exception mapping, and provides an interactive Web UI.
Strict Layer Rule: Presentation tier handles input/output only.
No business rules here. No direct database calls.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from data.database import init_db
from presentation.routes.book_routes import router as books_router
from business.exceptions import (
    BusinessRuleException,
    ValidationError,
    BookNotFoundError,
    OutOfStockError,
    DuplicateISBNError,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise database tables upon startup."""
    init_db()
    yield


app = FastAPI(
    title="Library Management System (3-Tier Architecture)",
    description=(
        "A 3-Tier Book Manager implementing complete separation of concerns "
        "across Presentation, Business Logic, and Data Access layers."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Global Exception Handlers: Map Business Exceptions to HTTP Status Codes
# ---------------------------------------------------------------------------
@app.exception_handler(ValidationError)
@app.exception_handler(OutOfStockError)
async def validation_error_handler(request: Request, exc: BusinessRuleException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": exc.__class__.__name__, "message": exc.message},
    )


@app.exception_handler(BookNotFoundError)
async def not_found_handler(request: Request, exc: BookNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": "BookNotFoundError", "message": exc.message},
    )


@app.exception_handler(DuplicateISBNError)
async def conflict_handler(request: Request, exc: DuplicateISBNError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"error": "DuplicateISBNError", "message": exc.message},
    )


# Register API Router
app.include_router(books_router, prefix="/api")


# ---------------------------------------------------------------------------
# Presentation Web UI & Welcome Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/info", tags=["System"])
def api_info():
    """System information endpoint."""
    return {
        "message": "Welcome to the 3-Tier Library Management System API",
        "architecture": "3-Tier (Presentation, Business, Data)",
        "documentation": "/docs",
        "health": "/health",
        "version": "1.0.0",
    }


@app.get("/health", tags=["System"])
def health():
    return {"status": "healthy"}


@app.get("/", response_class=HTMLResponse, tags=["Presentation UI"])
def index_ui():
    """Interactive Web UI for managing books in the library."""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Library Management System | 3-Tier Architecture</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', system-ui, sans-serif; }
        body { background: #0f172a; color: #f8fafc; padding: 2rem; min-height: 100vh; }
        .container { max-width: 1100px; margin: 0 auto; }
        header { text-align: center; margin-bottom: 2rem; padding-bottom: 1.5rem; border-bottom: 1px solid #334155; }
        h1 { font-size: 2.2rem; color: #38bdf8; margin-bottom: 0.5rem; }
        .badge-bar { display: flex; justify-content: center; gap: 0.8rem; margin-top: 0.8rem; flex-wrap: wrap; }
        .badge { background: #1e293b; border: 1px solid #475569; padding: 0.35rem 0.8rem; border-radius: 9999px; font-size: 0.85rem; color: #94a3b8; }
        .badge a { color: #38bdf8; text-decoration: none; }
        .badge a:hover { text-decoration: underline; }
        .card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3); }
        .card h2 { font-size: 1.25rem; color: #f1f5f9; margin-bottom: 1rem; border-bottom: 1px solid #334155; padding-bottom: 0.5rem; }
        .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 1rem; }
        label { display: block; font-size: 0.8rem; color: #94a3b8; margin-bottom: 0.3rem; }
        input { width: 100%; background: #0f172a; border: 1px solid #475569; color: #fff; padding: 0.6rem 0.8rem; border-radius: 6px; font-size: 0.95rem; }
        input:focus { outline: none; border-color: #38bdf8; }
        .btn { cursor: pointer; padding: 0.6rem 1.2rem; border-radius: 6px; font-weight: 600; border: none; transition: 0.15s; font-size: 0.9rem; }
        .btn-primary { background: #0284c7; color: #fff; }
        .btn-primary:hover { background: #0369a1; }
        .btn-success { background: #10b981; color: #fff; padding: 0.35rem 0.7rem; font-size: 0.85rem; }
        .btn-success:hover { background: #059669; }
        .btn-danger { background: #ef4444; color: #fff; padding: 0.35rem 0.7rem; font-size: 0.85rem; }
        .btn-danger:hover { background: #dc2626; }
        .search-bar { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
        .search-bar input { flex: 1; }
        table { width: 100%; border-collapse: collapse; text-align: left; }
        th { background: #0f172a; color: #94a3b8; padding: 0.8rem 1rem; font-size: 0.85rem; text-transform: uppercase; border-bottom: 2px solid #334155; }
        td { padding: 0.9rem 1rem; border-bottom: 1px solid #334155; font-size: 0.95rem; vertical-align: middle; }
        tr:hover { background: rgba(255, 255, 255, 0.02); }
        .qty-badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 6px; font-weight: bold; font-size: 0.85rem; }
        .qty-in-stock { background: #064e3b; color: #6ee7b7; }
        .qty-out { background: #7f1d1d; color: #fca5a5; }
        .actions { display: flex; gap: 0.5rem; }
        .alert { padding: 0.8rem 1rem; border-radius: 6px; margin-bottom: 1rem; font-size: 0.9rem; display: none; }
        .alert-error { background: #7f1d1d; color: #fecaca; border: 1px solid #b91c1c; }
        .alert-success { background: #064e3b; color: #a7f3d0; border: 1px solid #047857; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Library Management System</h1>
            <p style="color: #94a3b8;">A clean 3-Tier Architecture demonstration (Presentation | Business | Data)</p>
            <div class="badge-bar">
                <span class="badge">Architecture: <strong>3-Tier N-Tier</strong></span>
                <span class="badge">Tech Stack: <strong>Python + FastAPI + SQLite</strong></span>
                <span class="badge"><a href="/docs" target="_blank">&#128218; Interactive Swagger API Docs (/docs)</a></span>
                <span class="badge"><a href="/redoc" target="_blank">&#128196; ReDoc (/redoc)</a></span>
            </div>
        </header>

        <div id="alertBox" class="alert"></div>

        <!-- Add Book Form Card -->
        <div class="card">
            <h2>Add New Book</h2>
            <form id="addBookForm">
                <div class="form-grid">
                    <div>
                        <label>Title *</label>
                        <input type="text" id="title" placeholder="e.g. Clean Code" required>
                    </div>
                    <div>
                        <label>Author *</label>
                        <input type="text" id="author" placeholder="e.g. Robert Martin" required>
                    </div>
                    <div>
                        <label>ISBN (10 or 13 digits) *</label>
                        <input type="text" id="isbn" placeholder="e.g. 9780132350884" required>
                    </div>
                    <div>
                        <label>Publication Year *</label>
                        <input type="number" id="publication_year" placeholder="e.g. 2008" required>
                    </div>
                    <div>
                        <label>Quantity *</label>
                        <input type="number" id="quantity" value="1" min="0" required>
                    </div>
                </div>
                <button type="submit" class="btn btn-primary">+ Add Book to Catalog</button>
            </form>
        </div>

        <!-- Book Collection List Card -->
        <div class="card">
            <h2>Book Collection</h2>
            <div class="search-bar">
                <input type="text" id="searchInput" placeholder="Search books by title or author...">
                <button class="btn btn-primary" onclick="loadBooks()">Refresh</button>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Title</th>
                        <th>Author</th>
                        <th>ISBN</th>
                        <th>Year</th>
                        <th>Quantity</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="booksTableBody">
                    <tr><td colspan="7" style="text-align: center; color: #64748b;">Loading books...</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        const API_URL = '/api/books/';

        function showAlert(msg, isError = false) {
            const box = document.getElementById('alertBox');
            box.textContent = msg;
            box.className = 'alert ' + (isError ? 'alert-error' : 'alert-success');
            box.style.display = 'block';
            setTimeout(() => { box.style.display = 'none'; }, 4500);
        }

        async function loadBooks() {
            const query = document.getElementById('searchInput').value.trim();
            const url = query ? `${API_URL}?query=${encodeURIComponent(query)}` : API_URL;
            try {
                const res = await fetch(url);
                const books = await res.json();
                const tbody = document.getElementById('booksTableBody');
                if (books.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #64748b;">No books found. Add a book above!</td></tr>';
                    return;
                }
                tbody.innerHTML = books.map(b => `
                    <tr>
                        <td><strong>#${b.id}</strong></td>
                        <td style="font-weight: 600;">${b.title}</td>
                        <td style="color: #94a3b8;">${b.author}</td>
                        <td><code>${b.isbn}</code></td>
                        <td>${b.publication_year}</td>
                        <td>
                            <span class="qty-badge ${b.quantity > 0 ? 'qty-in-stock' : 'qty-out'}">
                                ${b.quantity} copy${b.quantity === 1 ? '' : 'ies'}
                            </span>
                        </td>
                        <td>
                            <div class="actions">
                                <button class="btn btn-success" onclick="checkoutBook(${b.id})" ${b.quantity <= 0 ? 'disabled style="opacity:0.5;cursor:not-allowed;"' : ''}>Check Out</button>
                                <button class="btn btn-danger" onclick="deleteBook(${b.id})">Delete</button>
                            </div>
                        </td>
                    </tr>
                `).join('');
            } catch (err) {
                showAlert("Failed to load books from API: " + err, true);
            }
        }

        document.getElementById('searchInput').addEventListener('input', () => {
            loadBooks();
        });

        document.getElementById('addBookForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const payload = {
                title: document.getElementById('title').value,
                author: document.getElementById('author').value,
                isbn: document.getElementById('isbn').value,
                publication_year: parseInt(document.getElementById('publication_year').value, 10),
                quantity: parseInt(document.getElementById('quantity').value, 10)
            };
            try {
                const res = await fetch(API_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (!res.ok) {
                    showAlert(data.message || data.detail || "Validation Error", true);
                } else {
                    showAlert(`Book "${data.title}" added successfully!`);
                    document.getElementById('addBookForm').reset();
                    loadBooks();
                }
            } catch (err) {
                showAlert("Error submitting book: " + err, true);
            }
        });

        async function checkoutBook(id) {
            try {
                const res = await fetch(`${API_URL}${id}/checkout`, { method: 'POST' });
                const data = await res.json();
                if (!res.ok) {
                    showAlert(data.message || "Failed to check out book", true);
                } else {
                    showAlert(`Checked out 1 copy of "${data.title}". Remaining: ${data.quantity}`);
                    loadBooks();
                }
            } catch (err) {
                showAlert("Error checking out: " + err, true);
            }
        }

        async function deleteBook(id) {
            if (!confirm(`Are you sure you want to remove book #${id}?`)) return;
            try {
                const res = await fetch(`${API_URL}${id}`, { method: 'DELETE' });
                const data = await res.json();
                if (!res.ok) {
                    showAlert(data.message || "Failed to delete book", true);
                } else {
                    showAlert(`Book #${id} deleted.`);
                    loadBooks();
                }
            } catch (err) {
                showAlert("Error deleting: " + err, true);
            }
        }

        loadBooks();
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)
