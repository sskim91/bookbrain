"""Tests for vector_db module."""

from unittest.mock import MagicMock

from bookbrain.core.config import settings
from bookbrain.core.vector_db import (
    delete_collection,
    ensure_collection_exists,
)


class TestEnsureCollectionExists:
    """Tests for ensure_collection_exists function."""

    def test_creates_collection_when_not_exists(self, mock_qdrant_client):
        """Test that collection is created when it doesn't exist."""
        mock_collections = MagicMock()
        mock_collections.collections = []
        mock_qdrant_client.get_collections.return_value = mock_collections

        result = ensure_collection_exists(client=mock_qdrant_client)

        assert result is True
        mock_qdrant_client.create_collection.assert_called_once()
        call_args = mock_qdrant_client.create_collection.call_args
        assert call_args.kwargs["collection_name"] == "chunks"
        assert call_args.kwargs["vectors_config"].size == settings.vector_size

    def test_skips_creation_when_exists(self, mock_qdrant_client):
        """Test that collection is not created when it already exists."""
        mock_collection = MagicMock()
        mock_collection.name = "chunks"
        mock_collections = MagicMock()
        mock_collections.collections = [mock_collection]
        mock_qdrant_client.get_collections.return_value = mock_collections

        result = ensure_collection_exists(client=mock_qdrant_client)

        assert result is False
        mock_qdrant_client.create_collection.assert_not_called()


class TestDeleteCollection:
    """Tests for delete_collection function."""

    def test_deletes_collection_when_exists(self, mock_qdrant_client):
        """Test that collection is deleted when it exists."""
        mock_collection = MagicMock()
        mock_collection.name = "chunks"
        mock_collections = MagicMock()
        mock_collections.collections = [mock_collection]
        mock_qdrant_client.get_collections.return_value = mock_collections

        result = delete_collection(client=mock_qdrant_client)

        assert result is True
        mock_qdrant_client.delete_collection.assert_called_once_with(
            collection_name="chunks"
        )

    def test_skips_deletion_when_not_exists(self, mock_qdrant_client):
        """Test that nothing happens when collection doesn't exist."""
        mock_collections = MagicMock()
        mock_collections.collections = []
        mock_qdrant_client.get_collections.return_value = mock_collections

        result = delete_collection(client=mock_qdrant_client)

        assert result is False
        mock_qdrant_client.delete_collection.assert_not_called()


class TestVectorSize:
    """Tests for vector size setting."""

    def test_vector_size_is_openai_dimension(self):
        """Test that vector size default matches OpenAI text-embedding-3."""
        assert settings.vector_size == 1536
