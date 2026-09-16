# 3-Tier Architecture Diagram & Specification

## 1. Overview of the 3-Tier Architecture

The **Library Management Application** strictly enforces separation of concerns across three decoupled tiers:

```text
+-----------------------------------------------------------------------------------+
|                        1. PRESENTATION TIER (/presentation)                       |
|                                                                                   |
|  * Interactive Web UI (HTML / CSS / Vanilla JavaScript) at http://localhost:8000/ |
|  * Interactive Swagger API Documentation at http://localhost:8000/docs           |
|  * FastAPI REST API Routers (/api/books)                                          |
|  * Pydantic DTO Schemas (BookCreate, BookUpdate, BookResponse)                    |
|  * Global Exception Handlers (translates domain errors into 400, 404, 409 HTTP)   |
|  * STRICT RULE: Handles I/O only. No business logic. No direct database calls.    |
+-----------------------------------------+-----------------------------------------+
                                          | Calls Service methods (DTO payloads)
                                          v
+-----------------------------------------------------------------------------------+
|                         2. BUSINESS TIER (/business)                              |
|                                                                                   |
|  * BookService (Domain orchestration & business rule enforcement)                 |
|  * Business Rules Enforced:                                                       |
|      - Title and Author cannot be empty                                           |
|      - Publication Year must be valid (not in the future)                         |
|      - ISBN must be exactly 10 or 13 digits                                       |
|      - Quantity cannot be negative                                                |
|      - Book cannot be checked out if quantity is 0 (raises OutOfStockError)       |
|  * Pure Domain Exceptions (ValidationError, BookNotFoundError, OutOfStockError)   |
|  * STRICT RULE: Depends ONLY on IBookRepository abstraction. Never imports DB.    |
+-----------------------------------------+-----------------------------------------+
                                          | Calls IBookRepository interface
                                          v
+-----------------------------------------------------------------------------------+
|                           3. DATA TIER (/data)                                    |
|                                                                                   |
|  * IBookRepository (Abstract Base Class / Interface)                              |
|  * Implementation A: BookRepository (SQLAlchemy ORM + SQLite database)            |
|  * Implementation B: InMemoryBookRepository (Pure Python in-memory list/dict)     |
|  * ORM Model: Book (id, title, author, isbn, publication_year, quantity)          |
|  * STRICT RULE: Performs data read/write only. No validation or display logic.    |
+-----------------------------------------+-----------------------------------------+
                                          | SQL queries / In-memory operations
                                          v
+-----------------------------------------------------------------------------------+
|                               STORAGE MEDIUM                                      |
|            SQLite Database (library.db)  OR  In-Memory Data Store                 |
+-----------------------------------------------------------------------------------+
```

---

## 2. Tier Separation & Communication Matrix

| Tier | Directory | Allowed Inputs | Allowed Outputs | Prohibited Actions |
|---|---|---|---|---|
| **Presentation** | `/presentation` | HTTP requests from browser/client | HTTP responses, JSON, HTML | **NO** SQL queries, **NO** business validation rules |
| **Business** | `/business` | Method calls from Presentation tier | Domain objects, custom domain exceptions | **NO** HTTP imports, **NO** direct DB calls, depends on `IBookRepository` only |
| **Data** | `/data` | Method calls from Business tier via `IBookRepository` | Entities (Book), raw query results | **NO** business rule validation, **NO** knowledge of how data is rendered |

---

## 3. Data Flow: "Check Out a Book" Transaction

```mermaid
sequenceDiagram
    autonumber
    actor User as User (Browser / API Client)
    participant Pres as Presentation Tier (/presentation)<br/>book_routes.py
    participant Biz as Business Tier (/business)<br/>BookService
    participant Repo as Data Tier (/data)<br/>IBookRepository
    participant DB as SQLite DB / Memory List

    User->>Pres: POST /api/books/{id}/checkout
    Pres->>Biz: checkout_book(book_id)
    Biz->>Repo: get_by_id(book_id)
    Repo->>DB: Query book by ID
    DB-->>Repo: Book record
    Repo-->>Biz: Book entity
    
    alt Book not found
        Biz-->>Pres: Raise BookNotFoundError
        Pres-->>User: HTTP 404 Not Found
    else Book quantity == 0
        Biz-->>Pres: Raise OutOfStockError ("Cannot check out; quantity is 0")
        Pres-->>User: HTTP 400 Bad Request ("Meaningful error message")
    else Book quantity > 0
        Biz->>Biz: book.quantity -= 1
        Biz->>Repo: update(book)
        Repo->>DB: Save updated quantity
        DB-->>Repo: Commit OK
        Repo-->>Biz: Updated Book
        Biz-->>Pres: Return Book entity
        Pres-->>User: HTTP 200 OK (Updated Book JSON / UI updated)
    end
```

---

## 4. Design Decision: Repository Pattern for Swappable Storage

> **Design Decision Justification:**  
> We introduced the `IBookRepository` abstract interface in the Data Tier to invert dependencies (`Dependency Inversion Principle`). By having the `BookService` depend solely on the abstract interface rather than a concrete SQLite or SQLAlchemy session, we achieved true loose coupling. This allowed us to build two swappable data layers—`BookRepository` (SQLite) and `InMemoryBookRepository` (in-memory list)—and run unit tests with 100% mocked data and zero database dependencies. The accompanying `swap_test.py` proves that the business logic behaves identically across both implementations without modifying a single line of business tier code.
