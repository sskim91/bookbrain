"""Tests for vector_repository module."""

from unittest.mock import MagicMock

from bookbrain.repositories.vector_repository import (
    ChunkData,
    delete_chunks_by_book_id,
    get_chunks_by_book_id,
    store_chunks,
)


class TestStoreChunks:
    """Tests for store_chunks function."""

    def test_store_chunks_empty_list(self, mock_qdrant_client):
        """Test storing empty chunk list returns 0."""
        result = store_chunks(chunks=[], client=mock_qdrant_client)

        assert result == 0
        mock_qdrant_client.upsert.assert_not_called()

    def test_store_chunks_single(self, mock_qdrant_client):
        """Test storing a single chunk."""
        chunks = [
            ChunkData(
                vector=[0.1] * 1536,
                book_id=1,
                page=42,
                content="Test content",
                model_version="text-embedding-3-small",
            )
        ]

        result = store_chunks(chunks=chunks, client=mock_qdrant_client)

        assert result == 1
        mock_qdrant_client.upsert.assert_called_once()
        call_args = mock_qdrant_client.upsert.call_args
        assert call_args.kwargs["collection_name"] == "chunks"
        assert len(call_args.kwargs["points"]) == 1

    def test_store_chunks_multiple(self, mock_qdrant_client):
        """Test storing multiple chunks."""
        chunks = [
            ChunkData(
                vector=[0.1] * 1536,
                book_id=1,
                page=i,
                content=f"Content {i}",
                model_version="text-embedding-3-small",
            )
            for i in range(5)
        ]

        result = store_chunks(chunks=chunks, client=mock_qdrant_client)

        assert result == 5
        call_args = mock_qdrant_client.upsert.call_args
        assert len(call_args.kwargs["points"]) == 5

    def test_store_chunks_payload_structure(self, mock_qdrant_client):
        """Test that stored chunks have correct payload structure."""
        chunks = [
            ChunkData(
                vector=[0.5] * 1536,
                book_id=42,
                page=10,
                content="Important text",
                model_version="text-embedding-3-large",
            )
        ]

        store_chunks(chunks=chunks, client=mock_qdrant_client)

        call_args = mock_qdrant_client.upsert.call_args
        point = call_args.kwargs["points"][0]
        assert point.payload["book_id"] == 42
        assert point.payload["page"] == 10
        assert point.payload["content"] == "Important text"
        assert point.payload["model_version"] == "text-embedding-3-large"


class TestDeleteChunksByBookId:
    """Tests for delete_chunks_by_book_id function."""

    def test_delete_chunks_success(self, mock_qdrant_client):
        """Test deleting chunks for a book."""
        result = delete_chunks_by_book_id(book_id=1, client=mock_qdrant_client)

        assert result is True
        mock_qdrant_client.delete.assert_called_once()
        call_args = mock_qdrant_client.delete.call_args
        assert call_args.kwargs["collection_name"] == "chunks"

    def test_delete_chunks_filter_structure(self, mock_qdrant_client):
        """Test that delete uses correct filter for book_id."""
        delete_chunks_by_book_id(book_id=42, client=mock_qdrant_client)

        call_args = mock_qdrant_client.delete.call_args
        points_selector = call_args.kwargs["points_selector"]
        assert points_selector.must[0].key == "book_id"
        assert points_selector.must[0].match.value == 42


class TestGetChunksByBookId:
    """Tests for get_chunks_by_book_id function."""

    def test_get_chunks_empty(self, mock_qdrant_client):
        """Test getting chunks when none exist."""
        mock_qdrant_client.scroll.return_value = ([], None)

        chunks = get_chunks_by_book_id(book_id=1, client=mock_qdrant_client)

        assert chunks == []

    def test_get_chunks_with_results(self, mock_qdrant_client):
        """Test getting chunks returns payloads."""
        mock_point1 = MagicMock()
        mock_point1.payload = {"book_id": 1, "page": 1, "content": "Text 1"}
        mock_point2 = MagicMock()
        mock_point2.payload = {"book_id": 1, "page": 2, "content": "Text 2"}
        mock_qdrant_client.scroll.return_value = ([mock_point1, mock_point2], None)

        chunks = get_chunks_by_book_id(book_id=1, client=mock_qdrant_client)

        assert len(chunks) == 2
        assert chunks[0]["page"] == 1
        assert chunks[1]["page"] == 2

    def test_get_chunks_filter_structure(self, mock_qdrant_client):
        """Test that scroll uses correct filter for book_id."""
        mock_qdrant_client.scroll.return_value = ([], None)

        get_chunks_by_book_id(book_id=42, client=mock_qdrant_client)

        call_args = mock_qdrant_client.scroll.call_args
        scroll_filter = call_args.kwargs["scroll_filter"]
        assert scroll_filter.must[0].key == "book_id"
        assert scroll_filter.must[0].match.value == 42
