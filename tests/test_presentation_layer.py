"""
Integration Tests for Presentation Tier: REST API Endpoints.
Verifies HTTP routing, parameter parsing, JSON responses, and HTTP status code mappings.
"""
import pytest


class TestPresentationLayer:
    def test_root_ui_and_system_endpoints(self, client):
        # Web UI
        ui_res = client.get("/")
        assert ui_res.status_code == 200
        assert "text/html" in ui_res.headers["content-type"]
        assert "Library Management System" in ui_res.text

        # API Info
        info_res = client.get("/api/info")
        assert info_res.status_code == 200
        assert "architecture" in info_res.json()

        # Health
        health_res = client.get("/health")
        assert health_res.status_code == 200
        assert health_res.json()["status"] == "healthy"

    def test_book_crud_and_checkout_lifecycle(self, client):
        # 1. Add Book (POST /api/books/)
        payload = {
            "title": "Clean Code",
            "author": "Robert C. Martin",
            "isbn": "9780132350884",
            "publication_year": 2008,
            "quantity": 2,
        }
        res = client.post("/api/books/", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["title"] == "Clean Code"
        assert data["quantity"] == 2
        book_id = data["id"]

        # 2. View All Books (GET /api/books/)
        list_res = client.get("/api/books/")
        assert list_res.status_code == 200
        assert len(list_res.json()) >= 1

        # 3. Search Books (GET /api/books/?query=martin)
        search_res = client.get("/api/books/?query=martin")
        assert search_res.status_code == 200
        assert any(b["id"] == book_id for b in search_res.json())

        # 4. View Single Book (GET /api/books/{id})
        get_res = client.get(f"/api/books/{book_id}")
        assert get_res.status_code == 200
        assert get_res.json()["isbn"] == "9780132350884"

        # 5. Check out Book (POST /api/books/{id}/checkout)
        # First checkout: quantity 2 -> 1
        co_res = client.post(f"/api/books/{book_id}/checkout")
        assert co_res.status_code == 200
        assert co_res.json()["quantity"] == 1

        # Second checkout: quantity 1 -> 0
        co_res2 = client.post(f"/api/books/{book_id}/checkout")
        assert co_res2.status_code == 200
        assert co_res2.json()["quantity"] == 0

        # Third checkout when quantity is 0 -> 400 Bad Request
        co_res3 = client.post(f"/api/books/{book_id}/checkout")
        assert co_res3.status_code == 400
        assert "quantity is already 0" in co_res3.json()["message"]

        # 6. Update Book (PUT /api/books/{id})
        update_res = client.put(f"/api/books/{book_id}", json={"quantity": 5})
        assert update_res.status_code == 200
        assert update_res.json()["quantity"] == 5

        # 7. Delete Book (DELETE /api/books/{id})
        del_res = client.delete(f"/api/books/{book_id}")
        assert del_res.status_code == 200

        # 8. Verify Book Not Found (GET /api/books/{id} -> 404)
        nf_res = client.get(f"/api/books/{book_id}")
        assert nf_res.status_code == 404

    def test_presentation_validation_error_responses(self, client):
        # Empty title -> 400
        res = client.post(
            "/api/books/",
            json={"title": "", "author": "A", "isbn": "9780132350884", "publication_year": 2020, "quantity": 1},
        )
        assert res.status_code == 400

        # Future publication year -> 400
        res2 = client.post(
            "/api/books/",
            json={"title": "T", "author": "A", "isbn": "9780132350884", "publication_year": 2099, "quantity": 1},
        )
        assert res2.status_code == 400

        # Invalid ISBN length -> 400
        res3 = client.post(
            "/api/books/",
            json={"title": "T", "author": "A", "isbn": "123", "publication_year": 2020, "quantity": 1},
        )
        assert res3.status_code == 400

        # Negative quantity -> 400
        res4 = client.post(
            "/api/books/",
            json={"title": "T", "author": "A", "isbn": "9780132350884", "publication_year": 2020, "quantity": -5},
        )
        assert res4.status_code == 400
