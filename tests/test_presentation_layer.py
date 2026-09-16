"""
Integration Tests for Presentation Tier: FastAPI HTTP Endpoints.
Verifies routing, request deserialisation, response serialisation, and HTTP status codes.
"""
import pytest


class TestPresentationLayer:
    def test_root_and_health(self, client):
        res = client.get("/")
        assert res.status_code == 200
        assert "architecture" in res.json()

        health_res = client.get("/health")
        assert health_res.status_code == 200
        assert health_res.json() == {"status": "healthy"}

    def test_book_crud_endpoints(self, client):
        # 1. Create book
        book_payload = {
            "isbn": "978-0131103627",
            "title": "The C Programming Language",
            "author": "Brian Kernighan, Dennis Ritchie",
            "category": "Computer Science",
            "total_copies": 4,
        }
        create_res = client.post("/api/books/", json=book_payload)
        assert create_res.status_code == 201
        data = create_res.json()
        assert data["title"] == "The C Programming Language"
        book_id = data["id"]

        # 2. Duplicate ISBN returns 409 Conflict
        dup_res = client.post("/api/books/", json=book_payload)
        assert dup_res.status_code == 409

        # 3. Get book by ID
        get_res = client.get(f"/api/books/{book_id}")
        assert get_res.status_code == 200
        assert get_res.json()["isbn"] == "9780131103627"

        # 4. List books with query
        list_res = client.get("/api/books/?search=programming")
        assert list_res.status_code == 200
        assert len(list_res.json()) >= 1

        # 5. Update book
        update_res = client.put(f"/api/books/{book_id}", json={"total_copies": 6})
        assert update_res.status_code == 200
        assert update_res.json()["total_copies"] == 6

        # 6. Delete book
        del_res = client.delete(f"/api/books/{book_id}")
        assert del_res.status_code == 200

        # 7. Verify deletion
        not_found_res = client.get(f"/api/books/{book_id}")
        assert not_found_res.status_code == 404

    def test_member_crud_endpoints(self, client):
        member_payload = {
            "name": "Grace Hopper",
            "email": "grace.hopper@navy.mil",
            "membership_type": "FACULTY",
            "custom_limit": 8,
        }
        res = client.post("/api/members/", json=member_payload)
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "Grace Hopper"
        assert data["max_borrow_limit"] == 8
        member_id = data["id"]

        # Duplicate email returns 409 Conflict
        dup_res = client.post("/api/members/", json=member_payload)
        assert dup_res.status_code == 409

        # Get member
        get_res = client.get(f"/api/members/{member_id}")
        assert get_res.status_code == 200

    def test_borrow_and_return_endpoints(self, client, sample_book, sample_member):
        # 1. Checkout book
        borrow_payload = {
            "member_id": sample_member.id,
            "book_id": sample_book.id,
            "loan_days": 14,
        }
        borrow_res = client.post("/api/borrow/", json=borrow_payload)
        assert borrow_res.status_code == 201
        rec = borrow_res.json()
        assert rec["status"] == "BORROWED"
        record_id = rec["id"]

        # 2. Check active loans endpoint for member
        loans_res = client.get(f"/api/members/{sample_member.id}/active-loans")
        assert loans_res.status_code == 200
        assert len(loans_res.json()) == 1

        # 3. Return book
        return_res = client.post(f"/api/borrow/return/{record_id}")
        assert return_res.status_code == 200
        assert return_res.json()["status"] == "RETURNED"

        # 4. Check active loans is now 0
        loans_res_after = client.get(f"/api/members/{sample_member.id}/active-loans")
        assert len(loans_res_after.json()) == 0
