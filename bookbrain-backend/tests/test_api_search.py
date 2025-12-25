"""Tests for the search API endpoints."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from bookbrain.main import app

client = TestClient(app)


class TestSearchAPI:
    """Tests for POST /api/search."""

    def test_search_returns_results(self):
        """Test successful search with results."""
        mock_results = {
            "results": [
                {
                    "book_id": 1,
                    "title": "Test Book",
                    "author": "Author",
                    "page": 10,
                    "content": "relevant content...",
                    "score": 0.85,
                }
            ],
            "total": 1,
            "query_time_ms": 150.5,
        }

        with patch(
            "bookbrain.api.routes.search.search_chunks",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = mock_results

            response = client.post(
                "/api/search",
                json={"query": "test query"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1
            assert data["results"][0]["score"] == 0.85
            assert data["results"][0]["book_id"] == 1
            assert data["results"][0]["title"] == "Test Book"
            assert "query_time_ms" in data

    def test_search_empty_results(self):
        """Test search with no matching results."""
        with patch(
            "bookbrain.api.routes.search.search_chunks",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = {"results": [], "total": 0, "query_time_ms": 50.0}

            response = client.post(
                "/api/search",
                json={"query": "nonexistent topic"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 0
            assert data["results"] == []

    def test_search_validates_empty_query(self):
        """Test that empty query is rejected."""
        response = client.post(
            "/api/search",
            json={"query": ""},
        )

        assert response.status_code == 422  # Validation error

    def test_search_validates_query_too_long(self):
        """Test that query over 500 chars is rejected."""
        long_query = "a" * 501

        response = client.post(
            "/api/search",
            json={"query": long_query},
        )

        assert response.status_code == 422  # Validation error

    def test_search_with_custom_limit(self):
        """Test search with custom limit parameter."""
        with patch(
            "bookbrain.api.routes.search.search_chunks",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = {"results": [], "total": 0, "query_time_ms": 50.0}

            response = client.post(
                "/api/search",
                json={"query": "test", "limit": 5},
            )

            assert response.status_code == 200
            mock.assert_called_once_with(
                query="test", limit=5, offset=0, min_score=None
            )

    def test_search_validates_limit_min(self):
        """Test that limit below 1 is rejected."""
        response = client.post(
            "/api/search",
            json={"query": "test", "limit": 0},
        )

        assert response.status_code == 422

    def test_search_validates_limit_max(self):
        """Test that limit above 50 is rejected."""
        response = client.post(
            "/api/search",
            json={"query": "test", "limit": 51},
        )

        assert response.status_code == 422

    def test_search_default_limit(self):
        """Test that default limit is 10."""
        with patch(
            "bookbrain.api.routes.search.search_chunks",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = {"results": [], "total": 0, "query_time_ms": 50.0}

            response = client.post(
                "/api/search",
                json={"query": "test"},
            )

            assert response.status_code == 200
            mock.assert_called_once_with(
                query="test", limit=10, offset=0, min_score=None
            )

    def test_search_with_offset_and_min_score(self):
        """Test search with offset and min_score parameters."""
        with patch(
            "bookbrain.api.routes.search.search_chunks",
            new_callable=AsyncMock,
        ) as mock:
            mock.return_value = {"results": [], "total": 0, "query_time_ms": 50.0}

            response = client.post(
                "/api/search",
                json={"query": "test", "offset": 10, "min_score": 0.7},
            )

            assert response.status_code == 200
            mock.assert_called_once_with(
                query="test", limit=10, offset=10, min_score=0.7
            )

    def test_search_validates_min_score_range(self):
        """Test that min_score above 1.0 is rejected."""
        response = client.post(
            "/api/search",
            json={"query": "test", "min_score": 1.5},
        )

        assert response.status_code == 422

    def test_search_embedding_error(self):
        """Test handling of embedding generation failure."""
        from bookbrain.core.exceptions import EmbeddingError

        with patch(
            "bookbrain.api.routes.search.search_chunks",
            new_callable=AsyncMock,
        ) as mock:
            mock.side_effect = EmbeddingError("OpenAI API error")

            response = client.post(
                "/api/search",
                json={"query": "test"},
            )

            assert response.status_code == 500
            data = response.json()
            assert data["detail"]["error"]["code"] == "EMBEDDING_FAILED"

    def test_search_general_error(self):
        """Test handling of general search failure."""
        with patch(
            "bookbrain.api.routes.search.search_chunks",
            new_callable=AsyncMock,
        ) as mock:
            mock.side_effect = Exception("Unexpected error")

            response = client.post(
                "/api/search",
                json={"query": "test"},
            )

            assert response.status_code == 500
            data = response.json()
            assert data["detail"]["error"]["code"] == "SEARCH_FAILED"
