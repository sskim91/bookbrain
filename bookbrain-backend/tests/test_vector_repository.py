"""Tests for vector_repository module."""

from unittest.mock import MagicMock

from bookbrain.core.config import settings
from bookbrain.repositories.vector_repository import (
    ChunkData,
    ChunkSearchResult,
    delete_chunks_by_book_id,
    get_chunks_by_book_id,
    search_similar_chunks,
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
                vector=[0.1] * settings.vector_size,
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
                vector=[0.1] * settings.vector_size,
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
                vector=[0.5] * settings.vector_size,
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


class TestSearchSimilarChunks:
    """Tests for search_similar_chunks function."""

    def test_search_empty_results(self, mock_qdrant_client):
        """Test search with no results."""
        mock_result = MagicMock()
        mock_result.points = []
        mock_qdrant_client.query_points.return_value = mock_result

        results = search_similar_chunks(
            query_vector=[0.1] * settings.vector_size,
            limit=10,
            client=mock_qdrant_client,
        )

        assert results == []

    def test_search_with_results(self, mock_qdrant_client):
        """Test search returns ChunkSearchResult objects."""
        mock_point1 = MagicMock()
        mock_point1.id = "uuid-1"
        mock_point1.score = 0.85
        mock_point1.payload = {
            "book_id": 1,
            "page": 10,
            "content": "Relevant content",
        }

        mock_point2 = MagicMock()
        mock_point2.id = "uuid-2"
        mock_point2.score = 0.75
        mock_point2.payload = {
            "book_id": 2,
            "page": 20,
            "content": "Another match",
        }

        mock_result = MagicMock()
        mock_result.points = [mock_point1, mock_point2]
        mock_qdrant_client.query_points.return_value = mock_result

        results = search_similar_chunks(
            query_vector=[0.1] * settings.vector_size,
            limit=10,
            client=mock_qdrant_client,
        )

        assert len(results) == 2
        assert isinstance(results[0], ChunkSearchResult)
        assert results[0].id == "uuid-1"
        assert results[0].book_id == 1
        assert results[0].page == 10
        assert results[0].content == "Relevant content"
        assert results[0].score == 0.85

    def test_search_calls_query_points_correctly(self, mock_qdrant_client):
        """Test that query_points is called with correct parameters."""
        mock_result = MagicMock()
        mock_result.points = []
        mock_qdrant_client.query_points.return_value = mock_result

        query_vec = [0.5] * settings.vector_size
        search_similar_chunks(
            query_vector=query_vec,
            limit=5,
            client=mock_qdrant_client,
        )

        mock_qdrant_client.query_points.assert_called_once()
        call_args = mock_qdrant_client.query_points.call_args
        assert call_args.kwargs["collection_name"] == "chunks"
        assert call_args.kwargs["query"] == query_vec
        assert call_args.kwargs["limit"] == 5
        assert call_args.kwargs["with_payload"] is True

    def test_search_filters_points_without_payload(self, mock_qdrant_client):
        """Test that points without payload are filtered out."""
        mock_point1 = MagicMock()
        mock_point1.id = "uuid-1"
        mock_point1.score = 0.85
        mock_point1.payload = {
            "book_id": 1,
            "page": 10,
            "content": "Valid content",
        }

        mock_point2 = MagicMock()
        mock_point2.id = "uuid-2"
        mock_point2.score = 0.75
        mock_point2.payload = None  # No payload

        mock_result = MagicMock()
        mock_result.points = [mock_point1, mock_point2]
        mock_qdrant_client.query_points.return_value = mock_result

        results = search_similar_chunks(
            query_vector=[0.1] * settings.vector_size,
            limit=10,
            client=mock_qdrant_client,
        )

        assert len(results) == 1
        assert results[0].id == "uuid-1"
