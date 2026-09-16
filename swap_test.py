"""
Swap Test Demonstration Script.
Assignment Requirement:
"Implement two versions of your data layer (e.g., SQLite and an in-memory list)
and demonstrate — in your README or a short script — that the business logic works
identically against both without any code changes to the business tier."
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from data.database import Base
# Data Layer Version 1: SQLite / SQLAlchemy Repository
from data.repositories.book_repository import BookRepository as SqliteBookRepository
# Data Layer Version 2: Pure Python In-Memory List Repository
from data.repositories.memory_repository import InMemoryBookRepository

# Unchanged Business Tier Service
from business.book_service import BookService
from business.exceptions import ValidationError, OutOfStockError


def run_test_scenario(repository, layer_name: str) -> dict:
    """
    Executes the exact same business logic scenario using the provided data layer.
    The BookService code is completely identical and unchanged.
    """
    print(f"\n-----------------------------------------------------------")
    print(f"  RUNNING SCENARIO WITH: [{layer_name}]")
    print(f"-----------------------------------------------------------")

    # Instantiate Business Tier with the injected Data Layer
    service = BookService(repository=repository)

    # Feature 1: Add a book
    b1 = service.add_book(
        title="Clean Code",
        author="Robert C. Martin",
        isbn="9780132350884",
        publication_year=2008,
        quantity=2,
    )
    b2 = service.add_book(
        title="The Mythical Man-Month",
        author="Frederick Brooks",
        isbn="9780201835953",
        publication_year=1995,
        quantity=1,
    )
    print(f"[OK] Added Book 1: '{b1.title}', Qty={b1.quantity}")
    print(f"[OK] Added Book 2: '{b2.title}', Qty={b2.quantity}")

    # Feature 2: View all books
    all_books = service.get_all_books()
    print(f"[OK] Total Books in collection: {len(all_books)}")

    # Feature 3: Search books (partial match)
    search_results = service.search_books("brooks")
    print(f"[OK] Search 'brooks' found: {[b.title for b in search_results]}")

    # Feature 4: Check out a book (quantity 2 -> 1)
    b1_after_co1 = service.checkout_book(b1.id)
    print(f"[OK] Checked out '{b1.title}': Quantity decreased to {b1_after_co1.quantity}")

    # Check out second copy (quantity 1 -> 0)
    b1_after_co2 = service.checkout_book(b1.id)
    print(f"[OK] Checked out '{b1.title}': Quantity decreased to {b1_after_co2.quantity}")

    # Feature 5: Check out fails when quantity is 0
    out_of_stock_caught = False
    try:
        service.checkout_book(b1.id)
    except OutOfStockError as e:
        out_of_stock_caught = True
        print(f"[OK] Enforced Business Rule: {e.message}")

    # Feature 6: Update book
    updated_b2 = service.update_book(b2.id, quantity=5)
    print(f"[OK] Updated '{b2.title}' quantity to: {updated_b2.quantity}")

    # Feature 7: Delete book
    service.delete_book(b2.id)
    remaining_books = service.get_all_books()
    print(f"[OK] Deleted Book 2. Remaining books: {len(remaining_books)}")

    return {
        "initial_count": len(all_books),
        "search_match_title": search_results[0].title,
        "b1_final_quantity": b1_after_co2.quantity,
        "out_of_stock_handled": out_of_stock_caught,
        "final_count_after_delete": len(remaining_books),
    }


def main():
    print("=================================================================")
    print("      DATA LAYER SWAP TEST: SQLITE vs IN-MEMORY LIST")
    print("=================================================================")

    # 1. Version 1: SQLite Data Layer
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    sqlite_db = Session()
    sqlite_repo = SqliteBookRepository(sqlite_db)
    sqlite_results = run_test_scenario(sqlite_repo, "DATA LAYER V1: SQLite Engine")

    # 2. Version 2: In-Memory List Data Layer
    memory_repo = InMemoryBookRepository()
    memory_results = run_test_scenario(memory_repo, "DATA LAYER V2: Pure In-Memory List")

    # 3. Compare outputs
    print("\n=================================================================")
    print("  COMPARING RESULTS ACROSS BOTH DATA LAYERS")
    print("=================================================================")
    print(f"{'Operation Metric':<28} | {'SQLite Layer':<14} | {'In-Memory List':<14} | {'Identical?':<10}")
    print("-" * 75)

    all_matched = True
    for key in sqlite_results:
        v1 = sqlite_results[key]
        v2 = memory_results[key]
        matched = (v1 == v2)
        if not matched:
            all_matched = False
        print(f"{key:<28} | {str(v1):<14} | {str(v2):<14} | {'YES' if matched else 'NO'}")

    print("-" * 75)
    if all_matched:
        print("\n[SUCCESS] SWAP TEST PASSED!")
        print("Both Data Layers produced 100% IDENTICAL business outcomes.")
        print("The Business Logic Tier required ZERO code modifications.")
    else:
        print("\n[FAILURE] Discrepancy detected between data layers!")
        exit(1)


if __name__ == "__main__":
    main()
