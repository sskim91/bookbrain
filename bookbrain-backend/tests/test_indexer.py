"""Tests for indexer service."""

from unittest.mock import AsyncMock, patch

import pytest

from bookbrain.core.config import settings
from bookbrain.core.exceptions import EmbeddingError, IndexingError
from bookbrain.models.chunker import Chunk, ChunkedDocument
from bookbrain.models.embedder import EmbeddedChunk, EmbeddingResult
from bookbrain.services.indexer import IndexingResult as IndexingResultModel
from bookbrain.services.indexer import index_book


class TestIndexBook:
    """Tests for index_book function."""

    @pytest.fixture
    def sample_chunked_document(self) -> ChunkedDocument:
        """Create a sample chunked document for testing."""
        return ChunkedDocument(
            chunks=[
                Chunk(index=0, content="Hello world", page_number=1, token_count=2),
                Chunk(index=1, content="Test content", page_number=1, token_count=2),
                Chunk(index=2, content="More text", page_number=2, token_count=2),
            ],
            total_chunks=3,
            source_pages=2,
        )

    @pytest.fixture
    def mock_embedding_result(self, sample_chunked_document) -> EmbeddingResult:
        """Create a mock embedding result."""
        return EmbeddingResult(
            embedded_chunks=[
                EmbeddedChunk(chunk=chunk, vector=[0.1] * settings.vector_size)
                for chunk in sample_chunked_document.chunks
            ],
            model_version="text-embedding-3-small",
            total_tokens=100,
        )

    @pytest.mark.asyncio
    async def test_index_book_success(
        self, sample_chunked_document, mock_embedding_result
    ):
        """Test successful book indexing."""
        with patch(
            "bookbrain.services.indexer.generate_embeddings",
            new_callable=AsyncMock,
        ) as mock_embed:
            with patch(
                "bookbrain.services.indexer.store_chunks"
            ) as mock_store:
                with patch(
                    "bookbrain.services.indexer.update_book_embedding_model",
                    new_callable=AsyncMock,
                ) as mock_update:
                    mock_embed.return_value = mock_embedding_result
                    mock_store.return_value = 3
                    mock_update.return_value = True

                    result = await index_book(
                        book_id=1, chunked_document=sample_chunked_document
                    )

                    assert isinstance(result, IndexingResultModel)
                    assert result.book_id == 1
                    assert result.chunks_stored == 3
                    assert result.model_version == "text-embedding-3-small"
                    assert result.total_tokens == 100

                    # Verify function calls
                    mock_embed.assert_called_once_with(sample_chunked_document.chunks)
                    mock_store.assert_called_once()
                    mock_update.assert_called_once_with(
                        book_id=1,
                        embedding_model="text-embedding-3-small",
                        total_pages=2,
                    )

    @pytest.mark.asyncio
    async def test_index_book_empty_document(self):
        """Test indexing an empty document."""
        empty_doc = ChunkedDocument(
            chunks=[],
            total_chunks=0,
            source_pages=0,
        )

        result = await index_book(book_id=1, chunked_document=empty_doc)

        assert result.book_id == 1
        assert result.chunks_stored == 0
        assert result.model_version == ""
        assert result.total_tokens == 0

    @pytest.mark.asyncio
    async def test_index_book_embedding_error_triggers_rollback(
        self, sample_chunked_document
    ):
        """Test that embedding error triggers rollback of stored chunks."""
        with patch(
            "bookbrain.services.indexer.generate_embeddings",
            new_callable=AsyncMock,
        ) as mock_embed:
            with patch(
                "bookbrain.services.indexer.delete_chunks_by_book_id"
            ) as mock_delete:
                mock_embed.side_effect = EmbeddingError("API error")

                with pytest.raises(IndexingError) as exc_info:
                    await index_book(
                        book_id=1, chunked_document=sample_chunked_document
                    )

                assert "Failed to index book 1" in str(exc_info.value)
                mock_delete.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_index_book_store_error_triggers_rollback(
        self, sample_chunked_document, mock_embedding_result
    ):
        """Test that store error triggers rollback."""
        with patch(
            "bookbrain.services.indexer.generate_embeddings",
            new_callable=AsyncMock,
        ) as mock_embed:
            with patch(
                "bookbrain.services.indexer.store_chunks"
            ) as mock_store:
                with patch(
                    "bookbrain.services.indexer.delete_chunks_by_book_id"
                ) as mock_delete:
                    mock_embed.return_value = mock_embedding_result
                    mock_store.side_effect = Exception("Qdrant error")

                    with pytest.raises(IndexingError) as exc_info:
                        await index_book(
                            book_id=1, chunked_document=sample_chunked_document
                        )

                    assert "Failed to index book 1" in str(exc_info.value)
                    mock_delete.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_index_book_db_update_error_triggers_rollback(
        self, sample_chunked_document, mock_embedding_result
    ):
        """Test that database update error triggers rollback."""
        with patch(
            "bookbrain.services.indexer.generate_embeddings",
            new_callable=AsyncMock,
        ) as mock_embed:
            with patch(
                "bookbrain.services.indexer.store_chunks"
            ) as mock_store:
                with patch(
                    "bookbrain.services.indexer.update_book_embedding_model",
                    new_callable=AsyncMock,
                ) as mock_update:
                    with patch(
                        "bookbrain.services.indexer.delete_chunks_by_book_id"
                    ) as mock_delete:
                        mock_embed.return_value = mock_embedding_result
                        mock_store.return_value = 3
                        mock_update.side_effect = Exception("Database error")

                        with pytest.raises(IndexingError):
                            await index_book(
                                book_id=1, chunked_document=sample_chunked_document
                            )

                        mock_delete.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_index_book_rollback_failure_is_ignored(
        self, sample_chunked_document
    ):
        """Test that rollback failure doesn't mask the original error."""
        with patch(
            "bookbrain.services.indexer.generate_embeddings",
            new_callable=AsyncMock,
        ) as mock_embed:
            with patch(
                "bookbrain.services.indexer.delete_chunks_by_book_id"
            ) as mock_delete:
                mock_embed.side_effect = EmbeddingError("API error")
                mock_delete.side_effect = Exception("Cleanup failed")

                with pytest.raises(IndexingError) as exc_info:
                    await index_book(
                        book_id=1, chunked_document=sample_chunked_document
                    )

                # Original error should be preserved
                assert "Failed to index book 1" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_index_book_creates_correct_chunk_data(
        self, sample_chunked_document, mock_embedding_result
    ):
        """Test that ChunkData is created correctly for Qdrant."""
        stored_chunks = None

        def capture_chunks(chunks):
            nonlocal stored_chunks
            stored_chunks = chunks
            return len(chunks)

        with patch(
            "bookbrain.services.indexer.generate_embeddings",
            new_callable=AsyncMock,
        ) as mock_embed:
            with patch(
                "bookbrain.services.indexer.store_chunks", side_effect=capture_chunks
            ):
                with patch(
                    "bookbrain.services.indexer.update_book_embedding_model",
                    new_callable=AsyncMock,
                ) as mock_update:
                    mock_embed.return_value = mock_embedding_result
                    mock_update.return_value = True

                    await index_book(
                        book_id=42, chunked_document=sample_chunked_document
                    )

                    assert stored_chunks is not None
                    assert len(stored_chunks) == 3

                    # Verify ChunkData structure
                    for i, chunk_data in enumerate(stored_chunks):
                        expected_chunk = sample_chunked_document.chunks[i]
                        assert chunk_data.book_id == 42
                        assert chunk_data.page == expected_chunk.page_number
                        assert chunk_data.content == expected_chunk.content
                        assert chunk_data.model_version == "text-embedding-3-small"
                        assert len(chunk_data.vector) == settings.vector_size


class TestIndexingResult:
    """Tests for IndexingResult model."""

    def test_indexing_result_creation(self):
        """Test IndexingResult model creation."""
        result = IndexingResultModel(
            book_id=1,
            chunks_stored=10,
            model_version="text-embedding-3-small",
            total_tokens=500,
        )

        assert result.book_id == 1
        assert result.chunks_stored == 10
        assert result.model_version == "text-embedding-3-small"
        assert result.total_tokens == 500
