# 3-Tier Architecture Library Management Application

A complete, production-ready **3-Tier "Library Management" Application** built with **Python FastAPI** and **SQLite/SQLAlchemy**, adhering strictly to the **3-Tier / N-Tier Architecture** pattern.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)](https://www.sqlalchemy.org/)
[![Tests](https://img.shields.io/badge/tests-17%20passed-brightgreen.svg)]()

---

## Table of Contents

- [Overview & Learning Objectives](#overview--learning-objectives)
- [Project Directory Structure](#project-directory-structure)
- [Tier Descriptions (Separation of Concerns)](#tier-descriptions-separation-of-concerns)
- [Design Decision Justification](#design-decision-justification)
- [Architecture Diagram](#architecture-diagram)
- [Features & Business Rules](#features--business-rules)
- [Step-by-Step Guide: How to Run the System](#step-by-step-guide-how-to-run-the-system)
  - [Where is the output shown?](#where-is-the-output-shown)
- [Running the Swap Test (Data Layer Independence)](#running-the-swap-test-data-layer-independence)
- [Running Automated Unit & Integration Tests](#running-automated-unit--integration-tests)
- [API Reference](#api-reference)

---

## Overview & Learning Objectives

This assignment demonstrates a clean **separation of concerns** across architectural layers:
- **Presentation Tier** (`/presentation`): Handles input/output and user interaction only. No business rules. No direct database calls.
- **Business Tier** (`/business`): Contains all validation and business rules. Never imports database libraries directly — depends only on the abstract `IBookRepository` interface.
- **Data Tier** (`/data`): Handles reading/writing data only. No validation logic. No display logic.

---

## Project Directory Structure

```text
Library_Management/
├── presentation/                 # TIER 1: Presentation Layer
│   ├── __init__.py
│   ├── main.py                   # FastAPI Application, Web UI, & Global Error Mapping
│   ├── schemas.py                # Pydantic DTO Schemas (Request/Response validation)
│   └── routes/
│       ├── __init__.py
│       └── book_routes.py        # REST API Endpoints (/api/books)
│
├── business/                     # TIER 2: Business Logic Layer
│   ├── __init__.py
│   ├── book_service.py           # Core Domain Service & Rule Enforcement
│   └── exceptions.py             # Pure Domain Exceptions (Decoupled from HTTP)
│
├── data/                         # TIER 3: Data Access Layer
│   ├── __init__.py
│   ├── database.py               # Engine, SessionLocal, & Base configuration
│   ├── models.py                 # SQLAlchemy ORM Model (Book)
│   └── repositories/
│       ├── __init__.py
│       ├── interfaces.py         # Abstract IBookRepository Contract
│       ├── book_repository.py    # Implementation A: SQLite / SQLAlchemy
│       └── memory_repository.py  # Implementation B: Pure In-Memory List
│
├── tests/                        # Automated Tests Layer
│   ├── __init__.py
│   ├── conftest.py               # Test fixtures (isolated SQLite + TestClient)
│   ├── test_business_mock.py    # Unit tests with Fake/Mock data layer (NO DATABASE)
│   ├── test_data_layer.py        # SQLite Repository tests
│   ├── test_presentation_layer.py# REST API Integration tests
│   └── test_swap.py              # Pytest verification of data layer swap
│
├── architecture_diagram.md       # Architecture specification with ASCII & Mermaid
├── architecture_diagram.png      # High-resolution visual architecture graphic
├── requirements.txt              # Project dependencies
├── run.py                        # Entry-point runner script
├── swap_test.py                  # Standalone executable Swap Test demonstration
├── .gitignore                    # Git ignore file
└── README.md                     # Documentation
```

---

## Tier Descriptions (Separation of Concerns)

### 1. Presentation Tier (`/presentation`)
- **What it does**: Exposes the user interface and HTTP REST API. It receives client input, parses JSON bodies/query parameters using Pydantic DTO schemas, invokes the appropriate business service method, and serializes domain objects into JSON or HTML responses.
- **Strict Boundary**: It contains **zero business rules** and makes **no direct database calls**. It maps domain exceptions (`ValidationError`, `OutOfStockError`, `BookNotFoundError`, `DuplicateISBNError`) into standard HTTP status codes (`400 Bad Request`, `404 Not Found`, `409 Conflict`).

### 2. Business Tier (`/business`)
- **What it does**: Contains all validation logic, domain invariants, and use cases in `BookService`.
- **Strict Boundary**: It **never imports database libraries directly** (no SQLAlchemy, no sqlite3). It interacts with the data layer exclusively through the `IBookRepository` interface. If validation fails, it raises pure Python domain exceptions (`BusinessRuleException` subclasses) without any HTTP framework dependencies.

### 3. Data Tier (`/data`)
- **What it does**: Manages persistent storage and retrieval. Contains entity models (`Book`) and repository implementations:
  - `BookRepository`: Uses SQLAlchemy ORM to query/persist records into SQLite (`library.db`).
  - `InMemoryBookRepository`: Uses pure Python dictionaries and lists for testing and data-layer swapping.
- **Strict Boundary**: Contains **no validation rules** (it trusts the business layer) and **no presentation/display knowledge**.

---

## Design Decision Justification

> **Design Decision:**  
> I used the **Repository Interface Pattern** (`IBookRepository`) to invert the dependency between the Business Logic Tier and the Data Access Tier (adhering to the *Dependency Inversion Principle*). By programming the `BookService` strictly to an abstract interface rather than a concrete SQLite or SQLAlchemy session, the business logic remains 100% decoupled from storage technology. This enabled us to implement two interchangeable data layer versions—a persistent SQLite repository (`BookRepository`) and an in-memory list/dictionary repository (`InMemoryBookRepository`). As demonstrated in our unit tests and `swap_test.py`, this allows the business logic to run identically against either data source without altering a single line of business tier code, while enabling fast, isolated unit testing that does not touch a real database.

---

## Architecture Diagram

The architecture is detailed in [architecture_diagram.md](architecture_diagram.md) and illustrated below:

![3-Tier Architecture Diagram](architecture_diagram.png)

```text
+-----------------------------------------------------------------------------------+
|                        1. PRESENTATION TIER (/presentation)                       |
|  * Interactive Web Dashboard (http://localhost:8000/)                             |
|  * Interactive Swagger Docs (http://localhost:8000/docs)                          |
|  * REST API Routers (/api/books) & Pydantic DTO Schemas                           |
+-----------------------------------------+-----------------------------------------+
                                          | Calls Service methods (DTO payloads)
                                          v
+-----------------------------------------------------------------------------------+
|                         2. BUSINESS TIER (/business)                              |
|  * BookService: Validation rules, stock decrement, checkout limits                |
|  * Pure Domain Exceptions (ValidationError, OutOfStockError, BookNotFoundError)   |
+-----------------------------------------+-----------------------------------------+
                                          | Calls abstract IBookRepository contract
                                          v
+-----------------------------------------------------------------------------------+
|                           3. DATA TIER (/data)                                    |
|  * IBookRepository (Abstract Interface)                                           |
|  * Version 1: BookRepository (SQLAlchemy + SQLite)                                |
|  * Version 2: InMemoryBookRepository (Pure In-Memory List/Dict)                   |
+-----------------------------------------+-----------------------------------------+
                                          | SQL / In-Memory operations
                                          v
+-----------------------------------------------------------------------------------+
|                   SQLite Database (.db)   OR   In-Memory Store                    |
+-----------------------------------------------------------------------------------+
```

---

## Features & Business Rules

### Implemented Features
1. **Add a Book**: Title, Author, ISBN, Publication Year, Quantity.
2. **View All Books**: List all books currently in the collection.
3. **Search Books**: Partial, case-insensitive match on Title or Author.
4. **Update a Book**: Edit any field of an existing book.
5. **Delete a Book**: Remove a book by ID.
6. **Check Out a Book**: Decrease quantity by 1 (must not go below 0).

### Enforced Business Rules (in `business/book_service.py`)
- **Title and Author cannot be empty**: Raises `ValidationError` if whitespace or blank.
- **Publication Year must be valid**: Cannot be in the future (compared to current UTC year).
- **ISBN must be exactly 10 or 13 digits**: Validated after stripping hyphens.
- **Quantity cannot be negative**: Must be $\ge 0$.
- **Check out guard**: Cannot check out a book if quantity is already 0; raises `OutOfStockError` with a clear message rather than crashing.

---

## Step-by-Step Guide: How to Run the System

### Step 1: Install Dependencies
Ensure Python 3.10+ is installed, then run:
```bash
pip install -r requirements.txt
```

### Step 2: Start the Application
Run the launcher script:
```bash
python run.py
```
*Terminal output:*
```text
Starting Library Management System on http://127.0.0.1:8000
Interactive API Documentation: http://127.0.0.1:8000/docs
INFO: Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO: Application startup complete.
```

### Where is the output shown?

Open your web browser and visit:

1. **Interactive Web UI**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
   - You will see the **Library Management System Dashboard**.
   - You can fill out the form to **Add a book**, search the collection live using the **Search bar**, and click **"Check Out"** to decrement copies or **"Delete"** to remove books.
   - Any validation error (e.g. invalid ISBN, future year, checking out 0 copies) is visibly shown in an alert banner.

2. **Interactive Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - Complete OpenAPI interactive documentation where you can execute every REST API endpoint directly from your browser.

3. **Raw JSON System Info**: [http://127.0.0.1:8000/api/info](http://127.0.0.1:8000/api/info)
   - Outputs API health and architectural metadata.

---

## Running the Swap Test (Data Layer Independence)

To prove that the Business Logic Tier is completely independent of the storage layer, run the included `swap_test.py`:

```bash
python swap_test.py
```

### What happens during the Swap Test?
1. The script runs an identical series of business operations against **Data Layer V1 (SQLite)**.
2. The script runs the exact same business operations against **Data Layer V2 (Pure In-Memory List)**.
3. It compares all outputs side-by-side and verifies that **both data layers produce 100% identical results** with **zero changes to the Business Logic tier**.

### Swap Test Terminal Output:
```text
=================================================================
      DATA LAYER SWAP TEST: SQLITE vs IN-MEMORY LIST
=================================================================

-----------------------------------------------------------
  RUNNING SCENARIO WITH: [DATA LAYER V1: SQLite Engine]
-----------------------------------------------------------
[OK] Added Book 1: 'Clean Code', Qty=2
[OK] Added Book 2: 'The Mythical Man-Month', Qty=1
[OK] Total Books in collection: 2
[OK] Search 'brooks' found: ['The Mythical Man-Month']
[OK] Checked out 'Clean Code': Quantity decreased to 1
[OK] Checked out 'Clean Code': Quantity decreased to 0
[OK] Enforced Business Rule: Cannot check out 'Clean Code'; quantity is already 0 (out of stock).
[OK] Updated 'The Mythical Man-Month' quantity to: 5
[OK] Deleted Book 2. Remaining books: 1

-----------------------------------------------------------
  RUNNING SCENARIO WITH: [DATA LAYER V2: Pure In-Memory List]
-----------------------------------------------------------
[OK] Added Book 1: 'Clean Code', Qty=2
[OK] Added Book 2: 'The Mythical Man-Month', Qty=1
[OK] Total Books in collection: 2
[OK] Search 'brooks' found: ['The Mythical Man-Month']
[OK] Checked out 'Clean Code': Quantity decreased to 1
[OK] Checked out 'Clean Code': Quantity decreased to 0
[OK] Enforced Business Rule: Cannot check out 'Clean Code'; quantity is already 0 (out of stock).
[OK] Updated 'The Mythical Man-Month' quantity to: 5
[OK] Deleted Book 2. Remaining books: 1

=================================================================
  COMPARING RESULTS ACROSS BOTH DATA LAYERS
=================================================================
Operation Metric             | SQLite Layer   | In-Memory List | Identical?
---------------------------------------------------------------------------
initial_count                | 2              | 2              | YES
search_match_title           | The Mythical Man-Month | The Mythical Man-Month | YES
b1_final_quantity            | 0              | 0              | YES
out_of_stock_handled         | True           | True           | YES
final_count_after_delete     | 1              | 1              | YES
---------------------------------------------------------------------------

[SUCCESS] SWAP TEST PASSED!
Both Data Layers produced 100% IDENTICAL business outcomes.
The Business Logic Tier required ZERO code modifications.
```

---

## Running Automated Unit & Integration Tests

Execute the test suite with Pytest:
```bash
python -m pytest -v tests/
```

### Test Suite Breakdown:
- **`tests/test_business_mock.py` (9 tests)**: Mandatory requirement: Unit tests for the Business Logic tier using a **fake/mock data source** (`InMemoryBookRepository`) that **does NOT hit a real database**.
- **`tests/test_data_layer.py` (4 tests)**: Tests the SQLite `BookRepository` CRUD operations in isolation.
- **`tests/test_presentation_layer.py` (3 tests)**: Integration tests testing REST endpoints, Web UI status, and error status code mappings via `TestClient`.
- **`tests/test_swap.py` (1 test)**: Automated pytest validation of the data layer swap.

### Test Results:
```text
tests/test_business_mock.py::test_mock_add_book_success PASSED           [  5%]
tests/test_business_mock.py::test_mock_rule1_title_and_author_cannot_be_empty PASSED [ 11%]
tests/test_business_mock.py::test_mock_rule2_publication_year_not_in_future PASSED [ 17%]
tests/test_business_mock.py::test_mock_rule3_isbn_must_be_10_or_13_digits PASSED [ 23%]
tests/test_business_mock.py::test_mock_rule4_quantity_cannot_be_negative PASSED [ 29%]
tests/test_business_mock.py::test_mock_rule5_checkout_fails_when_quantity_is_zero PASSED [ 35%]
tests/test_business_mock.py::test_mock_checkout_decreases_quantity_by_one PASSED [ 41%]
tests/test_business_mock.py::test_mock_duplicate_isbn_rejected PASSED    [ 47%]
tests/test_business_mock.py::test_mock_search_books_partial_match PASSED [ 52%]
tests/test_data_layer.py::TestBookRepository::test_add_and_get_book PASSED [ 58%]
tests/test_data_layer.py::TestBookRepository::test_search_books_by_title_and_author PASSED [ 64%]
tests/test_data_layer.py::TestBookRepository::test_update_book PASSED    [ 70%]
tests/test_data_layer.py::TestBookRepository::test_delete_book PASSED    [ 76%]
tests/test_presentation_layer.py::TestPresentationLayer::test_root_ui_and_system_endpoints PASSED [ 82%]
tests/test_presentation_layer.py::TestPresentationLayer::test_book_crud_and_checkout_lifecycle PASSED [ 88%]
tests/test_presentation_layer.py::TestPresentationLayer::test_presentation_validation_error_responses PASSED [ 94%]
tests/test_swap.py::test_swap_data_layer_identical_behavior PASSED       [100%]

======================== 17 passed in 1.17s ========================
```

---

## API Reference

All REST endpoints reside under the `/api/books` path:

| Method | Endpoint | Description | Status Code |
|---|---|---|---|
| `POST` | `/api/books/` | Add a new book (validates title, author, ISBN, year, quantity) | `201 Created` |
| `GET` | `/api/books/` | View all books in collection | `200 OK` |
| `GET` | `/api/books/?query={term}` | Search books by title or author (partial match) | `200 OK` |
| `GET` | `/api/books/{id}` | View single book details by ID | `200 OK` |
| `PUT` | `/api/books/{id}` | Edit any field of an existing book | `200 OK` |
| `DELETE` | `/api/books/{id}` | Remove a book by ID | `200 OK` |
| `POST` | `/api/books/{id}/checkout` | Check out a book (decreases quantity by 1) | `200 OK` |

