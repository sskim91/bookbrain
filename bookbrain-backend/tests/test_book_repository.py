"""Tests for book_repository module."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from bookbrain.repositories.book_repository import (
    create_book,
    delete_book,
    get_book,
    get_books,
)


class TestCreateBook:
    """Tests for create_book function."""

    @pytest.mark.asyncio
    async def test_create_book_with_connection(
        self, mock_db_connection, mock_db_cursor
    ):
        """Test creating a book with provided connection."""
        mock_db_cursor.fetchone.return_value = {"id": 42}

        book_id = await create_book(
            title="Test Book",
            file_path="/path/to/test.pdf",
            author="Test Author",
            conn=mock_db_connection,
        )

        assert book_id == 42
        mock_db_cursor.execute.assert_called_once()
        # Should NOT commit when connection is provided (caller manages transaction)
        mock_db_connection.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_book_auto_commit(self, mock_db_connection, mock_db_cursor):
        """Test creating a book without connection auto-commits."""
        mock_db_cursor.fetchone.return_value = {"id": 1}

        with patch("bookbrain.repositories.book_repository.get_db") as mock_get_db:
            mock_get_db.return_value.__aenter__ = AsyncMock(
                return_value=mock_db_connection
            )
            mock_get_db.return_value.__aexit__ = AsyncMock(return_value=None)

            book_id = await create_book(
                title="Auto Commit Book",
                file_path="/path/to/book.pdf",
            )

            assert book_id == 1
            mock_db_connection.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_book_raises_on_no_id(
        self, mock_db_connection, mock_db_cursor
    ):
        """Test that create_book raises when no ID is returned."""
        mock_db_cursor.fetchone.return_value = None

        with pytest.raises(RuntimeError, match="Failed to create book"):
            await create_book(
                title="Test Book",
                file_path="/path/to/test.pdf",
                conn=mock_db_connection,
            )


class TestGetBook:
    """Tests for get_book function."""

    @pytest.mark.asyncio
    async def test_get_book_found(self, mock_db_connection, mock_db_cursor):
        """Test getting an existing book."""
        mock_book = {
            "id": 1,
            "title": "Test Book",
            "author": "Author",
            "file_path": "/path/test.pdf",
            "total_pages": 100,
            "embedding_model": "text-embedding-3-small",
            "created_at": datetime.now(UTC),
        }
        mock_db_cursor.fetchone.return_value = mock_book

        book = await get_book(book_id=1, conn=mock_db_connection)

        assert book is not None
        assert book["id"] == 1
        assert book["title"] == "Test Book"

    @pytest.mark.asyncio
    async def test_get_book_not_found(self, mock_db_connection, mock_db_cursor):
        """Test getting a non-existent book."""
        mock_db_cursor.fetchone.return_value = None

        book = await get_book(book_id=999, conn=mock_db_connection)

        assert book is None


class TestGetBooks:
    """Tests for get_books function."""

    @pytest.mark.asyncio
    async def test_get_books_empty(self, mock_db_connection, mock_db_cursor):
        """Test getting books when none exist."""
        mock_db_cursor.fetchall.return_value = []

        books = await get_books(conn=mock_db_connection)

        assert books == []

    @pytest.mark.asyncio
    async def test_get_books_with_results(self, mock_db_connection, mock_db_cursor):
        """Test getting multiple books."""
        now = datetime.now(UTC)
        mock_books = [
            {
                "id": 1, "title": "Book 1", "author": None,
                "file_path": "/a.pdf", "total_pages": 50,
                "embedding_model": None, "created_at": now,
            },
            {
                "id": 2, "title": "Book 2", "author": "Author",
                "file_path": "/b.pdf", "total_pages": 100,
                "embedding_model": "model", "created_at": now,
            },
        ]
        mock_db_cursor.fetchall.return_value = mock_books

        books = await get_books(limit=10, offset=0, conn=mock_db_connection)

        assert len(books) == 2
        assert books[0]["title"] == "Book 1"
        assert books[1]["title"] == "Book 2"


class TestDeleteBook:
    """Tests for delete_book function."""

    @pytest.mark.asyncio
    async def test_delete_book_success(self, mock_db_connection, mock_db_cursor):
        """Test deleting an existing book."""
        mock_db_cursor.fetchone.return_value = {"id": 1}

        result = await delete_book(book_id=1, conn=mock_db_connection)

        assert result is True
        # Should NOT commit when connection is provided
        mock_db_connection.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_book_not_found(self, mock_db_connection, mock_db_cursor):
        """Test deleting a non-existent book."""
        mock_db_cursor.fetchone.return_value = None

        result = await delete_book(book_id=999, conn=mock_db_connection)

        assert result is False
