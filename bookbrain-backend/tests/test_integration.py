"""
Integration tests for database and vector store.

These tests require Docker containers to be running:
- PostgreSQL on localhost:5432
- Qdrant on localhost:6333

Run with: pytest tests/test_integration.py -v
Skip with: pytest -m "not integration"
"""

import pytest

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
skip_if_no_postgres = pytest.mark.skipif(
    not is_postgres_available(),
    reason="PostgreSQL not available (run docker-compose up -d)",
)
skip_if_no_qdrant = pytest.mark.skipif(
    not is_qdrant_available(),
    reason="Qdrant not available (run docker-compose up -d)",
)


@skip_if_no_postgres
class TestPostgreSQLIntegration:
    """Integration tests for PostgreSQL."""

    @pytest.fixture(autouse=True)
    async def setup_db(self):
        """Setup and teardown for each test."""
        from bookbrain.core.database import get_db

        # Cleanup before test
        async with get_db() as conn:
            await conn.execute(
                "DELETE FROM books WHERE title LIKE 'integration_test_%'"
            )
            await conn.commit()

        yield

        # Cleanup after test
        async with get_db() as conn:
            await conn.execute(
                "DELETE FROM books WHERE title LIKE 'integration_test_%'"
            )
            await conn.commit()

    @pytest.mark.asyncio
    async def test_create_and_get_book(self):
        """Test creating and retrieving a book from real PostgreSQL."""
        from bookbrain.repositories.book_repository import create_book, get_book

        # Create a book
        book_id = await create_book(
            title="integration_test_book",
            file_path="/tmp/test.pdf",
            author="Test Author",
            total_pages=100,
        )

        assert book_id > 0

        # Retrieve the book
        book = await get_book(book_id)

        assert book is not None
        assert book["title"] == "integration_test_book"
        assert book["author"] == "Test Author"
        assert book["total_pages"] == 100

    @pytest.mark.asyncio
    async def test_list_books(self):
        """Test listing books from real PostgreSQL."""
        from bookbrain.repositories.book_repository import (
            create_book,
            get_books,
        )

        # Create multiple books
        for i in range(3):
            await create_book(
                title=f"integration_test_list_{i}",
                file_path=f"/tmp/test_{i}.pdf",
            )

        # List books
        books = await get_books(limit=100)

        # Should have at least 3 books
        test_books = [b for b in books if b["title"].startswith("integration_test_")]
        assert len(test_books) >= 3

    @pytest.mark.asyncio
    async def test_delete_book(self):
        """Test deleting a book from real PostgreSQL."""
        from bookbrain.repositories.book_repository import (
            create_book,
            delete_book,
            get_book,
        )

        # Create a book
        book_id = await create_book(
            title="integration_test_delete",
            file_path="/tmp/test_delete.pdf",
        )

        # Delete the book
        deleted = await delete_book(book_id)
        assert deleted is True

        # Verify deletion
        book = await get_book(book_id)
        assert book is None


@skip_if_no_qdrant
class TestQdrantIntegration:
    """Integration tests for Qdrant."""

    @pytest.fixture(autouse=True)
    def setup_qdrant(self):
        """Setup and teardown for each test."""
        from bookbrain.core.vector_db import (
            ensure_collection_exists,
            get_qdrant_client,
        )

        # Ensure collection exists
        ensure_collection_exists()

        yield

        # Cleanup: delete test data
        client = get_qdrant_client()
        from bookbrain.repositories.vector_repository import delete_chunks_by_book_id

        # Delete test book chunks (book_id = 999999)
        delete_chunks_by_book_id(999999, client)

    def test_collection_creation(self):
        """Test that collection can be created."""
        from bookbrain.core.config import settings
        from bookbrain.core.vector_db import get_qdrant_client

        client = get_qdrant_client()
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]

        assert settings.qdrant_collection in collection_names

    def test_collection_has_correct_dimensions(self):
        """Test that collection has correct vector dimensions."""
        from bookbrain.core.config import settings
        from bookbrain.core.vector_db import get_qdrant_client

        client = get_qdrant_client()
        collection_info = client.get_collection(settings.qdrant_collection)

        # Check vector size matches settings
        assert collection_info.config.params.vectors.size == settings.vector_size

    def test_store_and_retrieve_chunks(self):
        """Test storing and retrieving chunks from real Qdrant."""
        from bookbrain.repositories.vector_repository import (
            ChunkData,
            delete_chunks_by_book_id,
            get_chunks_by_book_id,
            store_chunks,
        )

        test_book_id = 999999  # Use a unique ID for testing

        # Create test chunks with proper vector dimensions
        from bookbrain.core.config import settings

        test_vector = [0.1] * settings.vector_size

        chunks = [
            ChunkData(
                vector=test_vector,
                book_id=test_book_id,
                page=1,
                content="Test content page 1",
                model_version="test-model",
            ),
            ChunkData(
                vector=test_vector,
                book_id=test_book_id,
                page=2,
                content="Test content page 2",
                model_version="test-model",
            ),
        ]

        # Store chunks
        stored_count = store_chunks(chunks)
        assert stored_count == 2

        # Retrieve chunks
        retrieved = get_chunks_by_book_id(test_book_id)
        assert len(retrieved) == 2

        # Verify content
        contents = {chunk["content"] for chunk in retrieved}
        assert "Test content page 1" in contents
        assert "Test content page 2" in contents

        # Cleanup
        delete_chunks_by_book_id(test_book_id)

        # Verify deletion
        after_delete = get_chunks_by_book_id(test_book_id)
        assert len(after_delete) == 0


@skip_if_no_postgres
@skip_if_no_qdrant
class TestFullIntegration:
    """Full integration tests combining PostgreSQL and Qdrant."""

    @pytest.fixture(autouse=True)
    async def setup_all(self):
        """Setup and teardown for full integration tests."""
        from bookbrain.core.database import get_db
        from bookbrain.core.vector_db import ensure_collection_exists, get_qdrant_client
        from bookbrain.repositories.vector_repository import delete_chunks_by_book_id

        # Ensure collection exists
        ensure_collection_exists()

        yield

        # Cleanup PostgreSQL
        async with get_db() as conn:
            await conn.execute(
                "DELETE FROM books WHERE title LIKE 'full_integration_test_%'"
            )
            await conn.commit()

        # Cleanup Qdrant (delete chunks for test book IDs)
        client = get_qdrant_client()
        for book_id in range(990000, 990010):
            delete_chunks_by_book_id(book_id, client)

    @pytest.mark.asyncio
    async def test_book_with_chunks_workflow(self):
        """Test complete workflow: create book, store chunks, retrieve, delete."""
        from bookbrain.core.config import settings
        from bookbrain.repositories.book_repository import (
            create_book,
            delete_book,
            get_book,
        )
        from bookbrain.repositories.vector_repository import (
            ChunkData,
            delete_chunks_by_book_id,
            get_chunks_by_book_id,
            store_chunks,
        )

        # 1. Create book in PostgreSQL
        book_id = await create_book(
            title="full_integration_test_workflow",
            file_path="/tmp/workflow_test.pdf",
            author="Integration Test",
            total_pages=10,
            embedding_model="text-embedding-3-small",
        )

        assert book_id > 0

        # 2. Store chunks in Qdrant
        test_vector = [0.5] * settings.vector_size
        chunks = [
            ChunkData(
                vector=test_vector,
                book_id=book_id,
                page=i,
                content=f"Workflow test content page {i}",
                model_version="text-embedding-3-small",
            )
            for i in range(1, 4)
        ]

        stored = store_chunks(chunks)
        assert stored == 3

        # 3. Verify book exists
        book = await get_book(book_id)
        assert book is not None
        assert book["embedding_model"] == "text-embedding-3-small"

        # 4. Verify chunks exist
        retrieved_chunks = get_chunks_by_book_id(book_id)
        assert len(retrieved_chunks) == 3

        # 5. Delete book and chunks
        delete_chunks_by_book_id(book_id)
        deleted = await delete_book(book_id)

        assert deleted is True

        # 6. Verify cleanup
        book_after = await get_book(book_id)
        chunks_after = get_chunks_by_book_id(book_id)

        assert book_after is None
        assert len(chunks_after) == 0
