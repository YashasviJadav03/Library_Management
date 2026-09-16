# Architecture Diagram & Design Document

## 1. 3-Tier Architectural Overview

The **Library Management System** is designed strictly adhering to the classic **3-Tier / N-Tier Architecture** pattern. This enforces loose coupling, high cohesion, clear separation of concerns, and ease of maintainability.

```
+-----------------------------------------------------------------------------+
|                           PRESENTATION TIER (/presentation)                 |
|                                                                             |
|  +--------------------+   +----------------------+   +-------------------+  |
|  |  Book API Routes   |   |  Member API Routes   |   | Borrow API Routes |  |
|  |  (/api/books)      |   |  (/api/members)      |   | (/api/borrow)     |  |
|  +---------+----------+   +----------+-----------+   +---------+---------+  |
|            |                         |                         |            |
|            +-------------------------+-------------------------+            |
|                                      |                                      |
|                  Request Validation & Serialization (Pydantic DTOs)         |
|                  HTTP Exception Mapping & Status Codes (400, 404, 409)      |
+--------------------------------------|--------------------------------------+
                                       | Dependency Injection (Calls Service API)
                                       v
+-----------------------------------------------------------------------------+
|                            BUSINESS TIER (/business)                        |
|                                                                             |
|  +--------------------+   +----------------------+   +-------------------+  |
|  |    BookService     |   |    MemberService     |   |   BorrowService   |  |
|  +--------------------+   +----------------------+   +-------------------+  |
|  * ISBN Uniqueness        * Email Validation         * Checkout Limit Rule  |
|  * Catalog Constraints    * Membership Tier Quotas   * Stock Decrement      |
|  * Active Loan Checks     * Account Lifecycle        * Late Fee Fine Calc   |
|                                                                             |
|  Domain Exceptions: LibraryDomainException, BookNotAvailableError, etc.      |
+--------------------------------------|--------------------------------------+
                                       | Uses Repositories (ORM Independent)
                                       v
+-----------------------------------------------------------------------------+
|                              DATA TIER (/data)                              |
|                                                                             |
|  +--------------------+   +----------------------+   +-------------------+  |
|  |   BookRepository   |   |   MemberRepository   |   | BorrowRepository  |  |
|  +---------+----------+   +----------+-----------+   +---------+---------+  |
|            |                         |                         |            |
|  +---------v----------+   +----------v-----------+   +---------v---------+  |
|  |     Book Model     |   |     Member Model     |   | BorrowRecord Model|  |
|  +--------------------+   +----------------------+   +-------------------+  |
|                                                                             |
|               SQLAlchemy Session Management / Connection Engine             |
+--------------------------------------|--------------------------------------+
                                       | SQL / Transactions
                                       v
+-----------------------------------------------------------------------------+
|                               DATABASE ENGINE                               |
|                                 SQLite (.db)                                |
+-----------------------------------------------------------------------------+
```

---

## 2. Layer Responsibilities & Isolation Rules

| Layer | Directory | Responsibilities | Inbound Dependencies | Outbound Dependencies |
|---|---|---|---|---|
| **Presentation Tier** | `/presentation` | HTTP REST endpoints, URL routing, query parsing, request/response validation (Pydantic), error status code mapping | External HTTP Clients / Browsers | Business Services |
| **Business Tier** | `/business` | Domain logic, validation rules (limits, due dates, fines), workflow orchestration, pure Python domain exceptions | Presentation Tier | Data Repositories & Models |
| **Data Tier** | `/data` | Database connectivity, SQLAlchemy ORM entities, SQL persistence, transactional CRUD queries (Repository Pattern) | Business Tier | SQLite Database |

---

## 3. Transaction Workflow: Book Checkout (Borrow)

```mermaid
sequenceDiagram
    autonumber
    actor Client as HTTP Client (User / Frontend)
    participant Pres as Presentation Tier (/presentation)<br/>borrow_routes.py
    participant Biz as Business Tier (/business)<br/>BorrowService
    participant Data as Data Tier (/data)<br/>Repositories & SQLite

    Client->>Pres: POST /api/borrow (member_id, book_id, loan_days)
    Pres->>Pres: Validate payload schema (BorrowRequest DTO)
    Pres->>Biz: borrow_book(member_id, book_id, loan_days)
    
    Biz->>Data: member_repo.get_by_id(member_id)
    Data-->>Biz: Member entity
    Biz->>Biz: Check member is active

    Biz->>Data: borrow_repo.get_active_borrows_by_member(member_id)
    Data-->>Biz: Active loans list
    Biz->>Biz: Verify active_count < max_borrow_limit

    Biz->>Data: book_repo.get_by_id(book_id)
    Data-->>Biz: Book entity
    Biz->>Biz: Verify available_copies > 0

    Biz->>Data: book.available_copies -= 1 (update)
    Biz->>Data: borrow_repo.add(BorrowRecord)
    Data-->>Biz: Persisted BorrowRecord

    Biz-->>Pres: Return domain BorrowRecord
    Pres->>Pres: Serialize to BorrowRecordResponse DTO
    Pres-->>Client: HTTP 201 Created (JSON body)
```

---

## 4. Transaction Workflow: Book Return & Fine Calculation

```mermaid
sequenceDiagram
    autonumber
    actor Client as HTTP Client
    participant Pres as Presentation Tier (/presentation)<br/>borrow_routes.py
    participant Biz as Business Tier (/business)<br/>BorrowService
    participant Data as Data Tier (/data)<br/>Repositories & SQLite

    Client->>Pres: POST /api/borrow/return/{record_id}
    Pres->>Biz: return_book(record_id, return_time)
    Biz->>Data: borrow_repo.get_by_id(record_id)
    Data-->>Biz: BorrowRecord

    Biz->>Biz: Validate record.status == BORROWED
    Biz->>Biz: If return_date > due_date: fine = overdue_days * $1.00 / day
    Biz->>Biz: Set record.status = RETURNED, record.fine_amount = fine

    Biz->>Data: book.available_copies += 1 (update)
    Biz->>Data: borrow_repo.update(record)
    Data-->>Biz: Updated BorrowRecord

    Biz-->>Pres: Return updated domain record
    Pres-->>Client: HTTP 200 OK (record with return_date & fine_amount)
```

---

## 5. Architectural Isolation Highlights

1. **Independent Testing**: Each tier is unit tested in isolation (`test_data_layer.py`, `test_business_layer.py`, `test_presentation_layer.py`).
2. **Framework Agnostic Business Rules**: The business services do not import `fastapi` or `Request`/`Response` objects. If the presentation tier changes (e.g. CLI, gRPC, GraphQL), the business tier remains untouched.
3. **Database Independence**: The repository abstraction decouples the storage implementation from business consumers.
