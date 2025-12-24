"""Tests for Books API endpoints."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from bookbrain.main import app
from bookbrain.services.indexer import IndexingResult

client = TestClient(app)


class TestUploadBook:
    """Tests for POST /api/books."""

    def test_upload_valid_pdf_success(self):
        """Test successful PDF upload and indexing."""
        # Create a dummy PDF content
        pdf_content = b"%PDF-1.4 test content"

        with (
            patch(
                "bookbrain.api.routes.books.save_uploaded_file",
                new_callable=AsyncMock,
            ) as mock_save,
            patch(
                "bookbrain.api.routes.books.book_repository.create_book",
                new_callable=AsyncMock,
            ) as mock_create,
            patch(
                "bookbrain.api.routes.books.parse_pdf",
                new_callable=AsyncMock,
            ) as mock_parse,
            patch(
                "bookbrain.api.routes.books.chunk_text",
            ) as mock_chunk,
            patch(
                "bookbrain.api.routes.books.index_book",
                new_callable=AsyncMock,
            ) as mock_index,
        ):
            mock_save.return_value = "/tmp/test.pdf"
            mock_create.return_value = 1
            mock_parse.return_value = MagicMock(pages=[], total_pages=10)
            mock_chunk.return_value = MagicMock(chunks=[])
            mock_index.return_value = IndexingResult(
                book_id=1,
                chunks_stored=45,
                model_version="text-embedding-3-small",
                total_tokens=10000,
            )

            response = client.post(
                "/api/books",
                files={"file": ("test.pdf", pdf_content, "application/pdf")},
                data={"title": "Test Book", "author": "Test Author"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "indexed"
            assert data["book_id"] == 1
            assert data["chunks_count"] == 45

    def test_upload_invalid_file_extension(self):
        """Test rejection of non-PDF file extension."""
        response = client.post(
            "/api/books",
            files={"file": ("test.txt", b"text content", "text/plain")},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"]["code"] == "INVALID_FILE_FORMAT"

    def test_upload_invalid_content_type(self):
        """Test rejection of invalid content type."""
        # Use valid PDF magic number but wrong content type
        response = client.post(
            "/api/books",
            files={"file": ("test.pdf", b"%PDF-1.4 content", "image/png")},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"]["code"] == "INVALID_FILE_FORMAT"

    def test_upload_invalid_magic_number(self):
        """Test rejection of file with wrong magic number (security check)."""
        # File has .pdf extension and correct content-type but wrong header
        response = client.post(
            "/api/books",
            files={"file": ("malicious.pdf", b"not a real pdf", "application/pdf")},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"]["code"] == "INVALID_FILE_FORMAT"

    def test_upload_defaults_title_from_filename(self):
        """Test that title defaults to filename without extension."""
        pdf_content = b"%PDF-1.4 test content"

        with (
            patch(
                "bookbrain.api.routes.books.save_uploaded_file",
                new_callable=AsyncMock,
            ) as mock_save,
            patch(
                "bookbrain.api.routes.books.book_repository.create_book",
                new_callable=AsyncMock,
            ) as mock_create,
            patch(
                "bookbrain.api.routes.books.parse_pdf",
                new_callable=AsyncMock,
            ) as mock_parse,
            patch(
                "bookbrain.api.routes.books.chunk_text",
            ) as mock_chunk,
            patch(
                "bookbrain.api.routes.books.index_book",
                new_callable=AsyncMock,
            ) as mock_index,
        ):
            mock_save.return_value = "/tmp/test.pdf"
            mock_create.return_value = 1
            mock_parse.return_value = MagicMock(pages=[], total_pages=10)
            mock_chunk.return_value = MagicMock(chunks=[])
            mock_index.return_value = IndexingResult(
                book_id=1,
                chunks_stored=0,
                model_version="text-embedding-3-small",
                total_tokens=0,
            )

            response = client.post(
                "/api/books",
                files={
                    "file": (
                        "My Awesome Book.pdf",
                        pdf_content,
                        "application/pdf",
                    )
                },
            )

            assert response.status_code == 200
            # Check that create_book was called with the filename as title
            mock_create.assert_called_once()
            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs["title"] == "My Awesome Book"

    def test_upload_cleanup_on_indexing_failure(self):
        """Test that book record and file are cleaned up on indexing failure."""
        pdf_content = b"%PDF-1.4 test content"

        with (
            patch(
                "bookbrain.api.routes.books.save_uploaded_file",
                new_callable=AsyncMock,
            ) as mock_save,
            patch(
                "bookbrain.api.routes.books.book_repository.create_book",
                new_callable=AsyncMock,
            ) as mock_create,
            patch(
                "bookbrain.api.routes.books.book_repository.delete_book",
                new_callable=AsyncMock,
            ) as mock_delete,
            patch(
                "bookbrain.api.routes.books.parse_pdf",
                new_callable=AsyncMock,
            ) as mock_parse,
            patch("os.path.exists") as mock_exists,
            patch("os.remove") as mock_remove,
        ):
            from bookbrain.core.exceptions import IndexingError

            mock_save.return_value = "/tmp/test.pdf"
            mock_create.return_value = 1
            mock_parse.side_effect = IndexingError("Parse failed")
            mock_exists.return_value = True

            response = client.post(
                "/api/books",
                files={"file": ("test.pdf", pdf_content, "application/pdf")},
            )

            assert response.status_code == 500
            data = response.json()
            assert data["detail"]["error"]["code"] == "INDEXING_FAILED"

            # Verify cleanup was attempted
            mock_delete.assert_called_once_with(1)
            mock_remove.assert_called_once_with("/tmp/test.pdf")


class TestGetBooks:
    """Tests for GET /api/books."""

    def test_get_books_empty_list(self):
        """Test getting empty book list."""
        with patch(
            "bookbrain.api.routes.books.book_repository.get_books",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.return_value = []

            response = client.get("/api/books")

            assert response.status_code == 200
            data = response.json()
            assert data["books"] == []
            assert data["total"] == 0

    def test_get_books_with_results(self):
        """Test getting book list with results."""
        mock_books = [
            {
                "id": 1,
                "title": "Book 1",
                "author": "Author 1",
                "file_path": "/path/1.pdf",
                "total_pages": 100,
                "embedding_model": "text-embedding-3-small",
                "created_at": datetime(2024, 1, 1, 12, 0, 0),
            },
            {
                "id": 2,
                "title": "Book 2",
                "author": None,
                "file_path": "/path/2.pdf",
                "total_pages": 50,
                "embedding_model": "text-embedding-3-small",
                "created_at": datetime(2024, 1, 2, 12, 0, 0),
            },
        ]

        with patch(
            "bookbrain.api.routes.books.book_repository.get_books",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.return_value = mock_books

            response = client.get("/api/books")

            assert response.status_code == 200
            data = response.json()
            assert len(data["books"]) == 2
            assert data["total"] == 2
            assert data["books"][0]["title"] == "Book 1"
            assert data["books"][1]["author"] is None

    def test_get_books_with_pagination(self):
        """Test pagination parameters."""
        with patch(
            "bookbrain.api.routes.books.book_repository.get_books",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.return_value = []

            response = client.get("/api/books?limit=10&offset=20")

            assert response.status_code == 200
            mock_get.assert_called_once_with(limit=10, offset=20)


class TestDeleteBook:
    """Tests for DELETE /api/books/{id}."""

    def test_delete_existing_book(self):
        """Test successful book deletion."""
        mock_book = {
            "id": 1,
            "title": "Test Book",
            "author": "Author",
            "file_path": "/path/test.pdf",
            "total_pages": 100,
            "embedding_model": "text-embedding-3-small",
            "created_at": datetime(2024, 1, 1, 12, 0, 0),
        }

        with (
            patch(
                "bookbrain.api.routes.books.book_repository.get_book",
                new_callable=AsyncMock,
            ) as mock_get,
            patch(
                "bookbrain.api.routes.books.delete_chunks_by_book_id",
            ) as mock_delete_chunks,
            patch(
                "bookbrain.api.routes.books.book_repository.delete_book",
                new_callable=AsyncMock,
            ) as mock_delete,
            patch("os.path.exists") as mock_exists,
            patch("os.remove") as mock_remove,
        ):
            mock_get.return_value = mock_book
            mock_delete.return_value = True
            mock_exists.return_value = True

            response = client.delete("/api/books/1")

            assert response.status_code == 200
            data = response.json()
            assert data["deleted"] is True

            mock_delete_chunks.assert_called_once_with(1)
            mock_delete.assert_called_once_with(1)
            mock_remove.assert_called_once_with("/path/test.pdf")

    def test_delete_nonexistent_book(self):
        """Test 404 for missing book."""
        with patch(
            "bookbrain.api.routes.books.book_repository.get_book",
            new_callable=AsyncMock,
        ) as mock_get:
            mock_get.return_value = None

            response = client.delete("/api/books/999")

            assert response.status_code == 404
            data = response.json()
            assert data["detail"]["error"]["code"] == "BOOK_NOT_FOUND"

    def test_delete_continues_on_qdrant_failure(self):
        """Test that deletion continues even if Qdrant deletion fails."""
        mock_book = {
            "id": 1,
            "title": "Test Book",
            "author": None,
            "file_path": "/path/test.pdf",
            "total_pages": None,
            "embedding_model": None,
            "created_at": datetime(2024, 1, 1, 12, 0, 0),
        }

        with (
            patch(
                "bookbrain.api.routes.books.book_repository.get_book",
                new_callable=AsyncMock,
            ) as mock_get,
            patch(
                "bookbrain.api.routes.books.delete_chunks_by_book_id",
            ) as mock_delete_chunks,
            patch(
                "bookbrain.api.routes.books.book_repository.delete_book",
                new_callable=AsyncMock,
            ) as mock_delete,
            patch("os.path.exists") as mock_exists,
            patch("os.remove"),
        ):
            mock_get.return_value = mock_book
            mock_delete_chunks.side_effect = Exception("Qdrant error")
            mock_delete.return_value = True
            mock_exists.return_value = True

            response = client.delete("/api/books/1")

            # Should still succeed despite Qdrant error
            assert response.status_code == 200
            assert response.json()["deleted"] is True
