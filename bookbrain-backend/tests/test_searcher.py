"""Tests for the search service."""

from unittest.mock import AsyncMock, patch

import pytest

from bookbrain.repositories.vector_repository import ChunkSearchResult
from bookbrain.services.searcher import search_chunks


# Helper to create books map for batch lookup
def create_mock_books_map(book_ids: list[int]) -> dict:
    """Create a mock books map for testing."""
    return {
        book_id: {
            "id": book_id,
            "title": f"Test Book {book_id}",
            "author": f"Author {book_id}",
            "file_path": f"/path/to/{book_id}.pdf",
            "total_pages": 100,
            "embedding_model": "text-embedding-3-small",
            "created_at": "2025-01-01T00:00:00",
        }
        for book_id in book_ids
    }


class TestSearchChunks:
    """Tests for search_chunks function."""

    @pytest.mark.asyncio
    async def test_search_chunks_returns_results(self):
        """Test successful search with results."""
        mock_search_results = [
            ChunkSearchResult(
                id="uuid-1",
                book_id=1,
                page=10,
                content="This is relevant content about the topic.",
                score=0.85,
            ),
            ChunkSearchResult(
                id="uuid-2",
                book_id=1,
                page=20,
                content="Another relevant piece of information.",
                score=0.75,
            ),
        ]

        with patch(
            "bookbrain.services.searcher.generate_embedding",
            new_callable=AsyncMock,
        ) as mock_embed, patch(
            "bookbrain.services.searcher.search_similar_chunks"
        ) as mock_search, patch(
            "bookbrain.services.searcher.get_books_by_ids",
            new_callable=AsyncMock,
        ) as mock_get_books:
            mock_embed.return_value = [0.1] * 1536  # Mock embedding vector
            mock_search.return_value = mock_search_results
            mock_get_books.return_value = create_mock_books_map([1])

            result = await search_chunks("test query", limit=10)

            assert result["total"] == 2
            assert len(result["results"]) == 2
            assert result["results"][0]["book_id"] == 1
            assert result["results"][0]["title"] == "Test Book 1"
            assert result["results"][0]["score"] == 0.85
            assert result["results"][0]["page"] == 10
            assert "query_time_ms" in result
            assert result["query_time_ms"] >= 0

            mock_embed.assert_called_once_with("test query")
            mock_search.assert_called_once()
            # Verify batch lookup was used
            mock_get_books.assert_called_once_with([1])

    @pytest.mark.asyncio
    async def test_search_chunks_empty_results(self):
        """Test search with no matching results."""
        with patch(
            "bookbrain.services.searcher.generate_embedding",
            new_callable=AsyncMock,
        ) as mock_embed, patch(
            "bookbrain.services.searcher.search_similar_chunks"
        ) as mock_search, patch(
            "bookbrain.services.searcher.get_books_by_ids",
            new_callable=AsyncMock,
        ) as mock_get_books:
            mock_embed.return_value = [0.1] * 1536
            mock_search.return_value = []
            mock_get_books.return_value = {}

            result = await search_chunks("nonexistent topic", limit=10)

            assert result["total"] == 0
            assert result["results"] == []
            assert "query_time_ms" in result

    @pytest.mark.asyncio
    async def test_search_chunks_with_custom_limit(self):
        """Test search with custom limit."""
        with patch(
            "bookbrain.services.searcher.generate_embedding",
            new_callable=AsyncMock,
        ) as mock_embed, patch(
            "bookbrain.services.searcher.search_similar_chunks"
        ) as mock_search, patch(
            "bookbrain.services.searcher.get_books_by_ids",
            new_callable=AsyncMock,
        ) as mock_get_books:
            mock_embed.return_value = [0.1] * 1536
            mock_search.return_value = []
            mock_get_books.return_value = {}

            await search_chunks("test query", limit=5)

            mock_search.assert_called_once()
            call_args = mock_search.call_args
            assert call_args[1]["limit"] == 5

    @pytest.mark.asyncio
    async def test_search_chunks_filters_missing_books(self):
        """Test that results with missing book metadata are filtered out."""
        mock_search_results = [
            ChunkSearchResult(
                id="uuid-1",
                book_id=1,
                page=10,
                content="Content from existing book.",
                score=0.85,
            ),
            ChunkSearchResult(
                id="uuid-2",
                book_id=999,  # Book doesn't exist
                page=20,
                content="Content from missing book.",
                score=0.75,
            ),
        ]

        with patch(
            "bookbrain.services.searcher.generate_embedding",
            new_callable=AsyncMock,
        ) as mock_embed, patch(
            "bookbrain.services.searcher.search_similar_chunks"
        ) as mock_search, patch(
            "bookbrain.services.searcher.get_books_by_ids",
            new_callable=AsyncMock,
        ) as mock_get_books:
            mock_embed.return_value = [0.1] * 1536
            mock_search.return_value = mock_search_results
            # Return only book id=1, missing id=999
            mock_get_books.return_value = create_mock_books_map([1])

            result = await search_chunks("test query", limit=10)

            # Only 1 result should be returned (the one with existing book)
            assert result["total"] == 1
            assert result["results"][0]["book_id"] == 1

    @pytest.mark.asyncio
    async def test_search_chunks_measures_time(self):
        """Test that query time is measured."""
        with patch(
            "bookbrain.services.searcher.generate_embedding",
            new_callable=AsyncMock,
        ) as mock_embed, patch(
            "bookbrain.services.searcher.search_similar_chunks"
        ) as mock_search, patch(
            "bookbrain.services.searcher.get_books_by_ids",
            new_callable=AsyncMock,
        ) as mock_get_books:
            mock_embed.return_value = [0.1] * 1536
            mock_search.return_value = []
            mock_get_books.return_value = {}

            result = await search_chunks("test query")

            assert "query_time_ms" in result
            assert isinstance(result["query_time_ms"], float)
            assert result["query_time_ms"] >= 0
