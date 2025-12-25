"""
Integration tests for API endpoints with real databases.

These tests use real PostgreSQL and Qdrant instances.
Run with: pytest tests/test_api_integration.py -v
Skip with: pytest -m "not integration"
"""

import pytest
from fastapi.testclient import TestClient

from bookbrain.main import app

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


def is_postgres_available() -> bool:
    """Check if PostgreSQL is available."""
    try:
        import psycopg

        conn = psycopg.connect(
            "postgresql://bookbrain:bookbrain@localhost:5432/bookbrain",
            connect_timeout=2,
        )
        conn.close()
        return True
    except Exception:
        return False


def is_qdrant_available() -> bool:
    """Check if Qdrant is available."""
    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(url="http://localhost:6333", timeout=2)
        client.get_collections()
        return True
    except Exception:
        return False


# Skip conditions
skip_if_no_db = pytest.mark.skipif(
    not (is_postgres_available() and is_qdrant_available()),
    reason="PostgreSQL or Qdrant not available (run docker-compose up -d)",
)

client = TestClient(app)


@skip_if_no_db
class TestBooksAPIIntegration:
    """Integration tests for Books API with real databases."""

    @pytest.fixture(autouse=True)
    async def setup_db(self):
        """Setup and teardown for each test."""
        from bookbrain.core.database import get_db
        from bookbrain.core.vector_db import ensure_collection_exists
        from bookbrain.repositories.vector_repository import delete_chunks_by_book_id

        # Ensure Qdrant collection exists
        ensure_collection_exists()

        yield

        # Cleanup: delete test books and their chunks
        async with get_db() as conn:
            # Get test book IDs
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT id FROM books WHERE title LIKE 'api_integration_test_%'"
                )
                rows = await cur.fetchall()
                test_ids = [row["id"] for row in rows]

            # Delete chunks for test books
            for book_id in test_ids:
                try:
                    delete_chunks_by_book_id(book_id)
                except Exception:
                    pass

            # Delete test books
            await conn.execute(
                "DELETE FROM books WHERE title LIKE 'api_integration_test_%'"
            )
            await conn.commit()

    def test_get_books_empty(self):
        """Test GET /api/books returns empty list initially (for test books)."""
        response = client.get("/api/books")

        assert response.status_code == 200
        data = response.json()
        assert "books" in data
        assert "total" in data
        assert isinstance(data["books"], list)

    def test_get_books_pagination(self):
        """Test GET /api/books with pagination parameters."""
        response = client.get("/api/books?limit=5&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert "books" in data

    def test_delete_nonexistent_book(self):
        """Test DELETE /api/books/{id} for non-existent book."""
        response = client.delete("/api/books/999999")

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"]["code"] == "BOOK_NOT_FOUND"

    def test_upload_invalid_file_format(self):
        """Test POST /api/books rejects non-PDF files."""
        response = client.post(
            "/api/books",
            files={"file": ("test.txt", b"plain text content", "text/plain")},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"]["code"] == "INVALID_FILE_FORMAT"

    def test_upload_fake_pdf(self):
        """Test POST /api/books rejects files with wrong magic number."""
        # Has .pdf extension but not a real PDF
        response = client.post(
            "/api/books",
            files={"file": ("fake.pdf", b"not a real pdf", "application/pdf")},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"]["code"] == "INVALID_FILE_FORMAT"


@skip_if_no_db
class TestHealthAPIIntegration:
    """Integration tests for Health API."""

    def test_health_check(self):
        """Test GET /api/health returns OK."""
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
