"""
Test demonstrating Data Layer Swapping in Pytest.
Verifies that BookService behaves identically with SQLite vs In-Memory Repositories.
"""
from datetime import datetime
from data.repositories.book_repository import BookRepository as SqliteRepo
from data.repositories.memory_repository import InMemoryBookRepository as MemoryRepo
from business.book_service import BookService
from business.exceptions import OutOfStockError


def test_swap_data_layer_identical_behavior(db_session):
    sqlite_repo = SqliteRepo(db_session)
    memory_repo = MemoryRepo()

    sqlite_service = BookService(repository=sqlite_repo)
    memory_service = BookService(repository=memory_repo)

    # 1. Add books in both
    b_sqlite = sqlite_service.add_book("Test Book", "Author", "9780132350884", 2015, quantity=1)
    b_memory = memory_service.add_book("Test Book", "Author", "9780132350884", 2015, quantity=1)

    assert b_sqlite.title == b_memory.title
    assert b_sqlite.quantity == b_memory.quantity == 1

    # 2. Check out book in both
    b_sqlite = sqlite_service.checkout_book(b_sqlite.id)
    b_memory = memory_service.checkout_book(b_memory.id)

    assert b_sqlite.quantity == b_memory.quantity == 0

    # 3. Second check out fails in both
    try:
        sqlite_service.checkout_book(b_sqlite.id)
        assert False, "Should have raised OutOfStockError"
    except OutOfStockError:
        pass

    try:
        memory_service.checkout_book(b_memory.id)
        assert False, "Should have raised OutOfStockError"
    except OutOfStockError:
        pass

    # 4. Search works identically in both
    res_sql = sqlite_service.search_books("test")
    res_mem = memory_service.search_books("test")

    assert len(res_sql) == len(res_mem) == 1
