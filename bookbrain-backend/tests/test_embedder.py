"""Tests for embedding service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bookbrain.core.exceptions import EmbeddingError, OpenAIKeyMissingError
from bookbrain.models.chunker import Chunk
from bookbrain.services.embedder import generate_embeddings


class TestGenerateEmbeddings:
    """Tests for generate_embeddings function."""

    @pytest.fixture
    def sample_chunks(self) -> list[Chunk]:
        """Create sample chunks for testing."""
        return [
            Chunk(index=0, content="Hello world", page_number=1, token_count=2),
            Chunk(index=1, content="Test content", page_number=1, token_count=2),
            Chunk(index=2, content="More text here", page_number=2, token_count=3),
        ]

    @pytest.fixture
    def mock_openai_response(self):
        """Create mock OpenAI embeddings response."""
        response = MagicMock()
        response.data = [
            MagicMock(embedding=[0.1] * 1536, index=0),
            MagicMock(embedding=[0.2] * 1536, index=1),
            MagicMock(embedding=[0.3] * 1536, index=2),
        ]
        response.model = "text-embedding-3-small"
        response.usage = MagicMock(total_tokens=100)
        return response

    @pytest.mark.asyncio
    async def test_generate_embeddings_success(
        self, sample_chunks, mock_openai_response
    ):
        """Test successful embedding generation."""
        with patch(
            "bookbrain.services.embedder._get_openai_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.embeddings.create = AsyncMock(return_value=mock_openai_response)
            mock_get_client.return_value = mock_client

            result = await generate_embeddings(sample_chunks)

            assert len(result.embedded_chunks) == 3
            assert result.model_version == "text-embedding-3-small"
            assert result.total_tokens == 100

            # Verify each embedded chunk
            for i, ec in enumerate(result.embedded_chunks):
                assert ec.chunk == sample_chunks[i]
                assert len(ec.vector) == 1536

    @pytest.mark.asyncio
    async def test_generate_embeddings_empty_list(self):
        """Test embedding generation with empty chunk list."""
        result = await generate_embeddings([])

        assert len(result.embedded_chunks) == 0
        assert result.total_tokens == 0

    @pytest.mark.asyncio
    async def test_generate_embeddings_preserves_chunk_order(
        self, sample_chunks, mock_openai_response
    ):
        """Test that chunk order is preserved in results."""
        with patch(
            "bookbrain.services.embedder._get_openai_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.embeddings.create = AsyncMock(return_value=mock_openai_response)
            mock_get_client.return_value = mock_client

            result = await generate_embeddings(sample_chunks)

            # Verify order matches input
            for i, ec in enumerate(result.embedded_chunks):
                assert ec.chunk.index == i
                assert ec.chunk.content == sample_chunks[i].content

    @pytest.mark.asyncio
    async def test_generate_embeddings_api_key_missing(self, sample_chunks):
        """Test error when OpenAI API key is not configured."""
        with patch("bookbrain.services.embedder.settings") as mock_settings:
            mock_settings.openai_api_key = ""
            # Reset the cached client
            with patch("bookbrain.services.embedder._client", None):
                with pytest.raises(OpenAIKeyMissingError):
                    await generate_embeddings(sample_chunks)

    @pytest.mark.asyncio
    async def test_generate_embeddings_vector_dimensions(
        self, sample_chunks, mock_openai_response
    ):
        """Test that vectors have correct dimensions (1536 for text-embedding-3)."""
        with patch(
            "bookbrain.services.embedder._get_openai_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.embeddings.create = AsyncMock(return_value=mock_openai_response)
            mock_get_client.return_value = mock_client

            result = await generate_embeddings(sample_chunks)

            for ec in result.embedded_chunks:
                assert len(ec.vector) == 1536


class TestEmbedderRetryLogic:
    """Tests for retry logic in embedding service."""

    @pytest.fixture
    def sample_chunk(self) -> list[Chunk]:
        """Create a single sample chunk for testing."""
        return [Chunk(index=0, content="Test", page_number=1, token_count=1)]

    @pytest.mark.asyncio
    async def test_retry_on_rate_limit_success_after_retry(self, sample_chunk):
        """Test successful retry after rate limit error."""
        from openai import RateLimitError

        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536, index=0)]
        mock_response.model = "text-embedding-3-small"
        mock_response.usage = MagicMock(total_tokens=10)

        call_count = 0

        async def mock_create(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RateLimitError(
                    "Rate limit exceeded",
                    response=MagicMock(status_code=429),
                    body=None,
                )
            return mock_response

        with patch(
            "bookbrain.services.embedder._get_openai_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.embeddings.create = mock_create
            mock_get_client.return_value = mock_client

            with patch("bookbrain.services.embedder.settings") as mock_settings:
                mock_settings.embedding_model = "text-embedding-3-small"
                mock_settings.embedding_batch_size = 100
                mock_settings.embedding_max_retries = 3
                mock_settings.embedding_retry_base_delay = 0.01  # Fast for testing

                result = await generate_embeddings(sample_chunk)

                assert call_count == 2  # First failed, second succeeded
                assert len(result.embedded_chunks) == 1

    @pytest.mark.asyncio
    async def test_retry_exhausted_raises_error(self, sample_chunk):
        """Test that EmbeddingError is raised after all retries exhausted."""
        from openai import RateLimitError

        async def mock_create(*args, **kwargs):
            raise RateLimitError(
                "Rate limit exceeded",
                response=MagicMock(status_code=429),
                body=None,
            )

        with patch(
            "bookbrain.services.embedder._get_openai_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.embeddings.create = mock_create
            mock_get_client.return_value = mock_client

            with patch("bookbrain.services.embedder.settings") as mock_settings:
                mock_settings.embedding_model = "text-embedding-3-small"
                mock_settings.embedding_batch_size = 100
                mock_settings.embedding_max_retries = 3
                mock_settings.embedding_retry_base_delay = 0.01

                with pytest.raises(EmbeddingError) as exc_info:
                    await generate_embeddings(sample_chunk)

                assert "Rate limit exceeded after" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_api_error_raises_immediately(self, sample_chunk):
        """Test that API errors are raised immediately without retry."""
        from openai import APIError

        async def mock_create(*args, **kwargs):
            raise APIError(
                "API Error",
                request=MagicMock(),
                body=None,
            )

        with patch(
            "bookbrain.services.embedder._get_openai_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.embeddings.create = mock_create
            mock_get_client.return_value = mock_client

            with pytest.raises(EmbeddingError) as exc_info:
                await generate_embeddings(sample_chunk)

            assert "OpenAI API error" in str(exc_info.value)


class TestBatchProcessing:
    """Tests for batch processing in embedding service."""

    @pytest.mark.asyncio
    async def test_batch_processing_multiple_batches(self):
        """Test that large chunk lists are processed in batches."""
        # Create 150 chunks (should be processed in 2 batches with size 100)
        chunks = [
            Chunk(index=i, content=f"Content {i}", page_number=1, token_count=2)
            for i in range(150)
        ]

        async def mock_create(*args, **kwargs):
            input_texts = kwargs.get("input", args[0] if args else [])
            response = MagicMock()
            response.data = [
                MagicMock(embedding=[0.1] * 1536, index=i)
                for i in range(len(input_texts))
            ]
            response.model = "text-embedding-3-small"
            response.usage = MagicMock(total_tokens=len(input_texts) * 10)
            return response

        with patch(
            "bookbrain.services.embedder._get_openai_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.embeddings.create = AsyncMock(side_effect=mock_create)
            mock_get_client.return_value = mock_client

            with patch("bookbrain.services.embedder.settings") as mock_settings:
                mock_settings.embedding_model = "text-embedding-3-small"
                mock_settings.embedding_batch_size = 100
                mock_settings.embedding_max_retries = 3
                mock_settings.embedding_retry_base_delay = 1.0

                result = await generate_embeddings(chunks)

                # Verify API calls
                assert mock_client.embeddings.create.call_count == 2
                
                # Check arguments of each call
                calls = mock_client.embeddings.create.call_args_list
                
                # First batch: 0-99
                args1, kwargs1 = calls[0]
                batch1_input = kwargs1["input"]
                assert len(batch1_input) == 100
                assert batch1_input[0] == "Content 0"
                assert batch1_input[99] == "Content 99"
                
                # Second batch: 100-149
                args2, kwargs2 = calls[1]
                batch2_input = kwargs2["input"]
                assert len(batch2_input) == 50
                assert batch2_input[0] == "Content 100"
                assert batch2_input[49] == "Content 149"

                assert len(result.embedded_chunks) == 150

    @pytest.mark.asyncio
    async def test_single_batch_small_list(self):
        """Test that small chunk lists are processed in single batch."""
        chunks = [
            Chunk(index=i, content=f"Content {i}", page_number=1, token_count=2)
            for i in range(10)
        ]

        call_count = 0

        async def mock_create(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            response = MagicMock()
            response.data = [
                MagicMock(embedding=[0.1] * 1536, index=i) for i in range(10)
            ]
            response.model = "text-embedding-3-small"
            response.usage = MagicMock(total_tokens=50)
            return response

        with patch(
            "bookbrain.services.embedder._get_openai_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.embeddings.create = mock_create
            mock_get_client.return_value = mock_client

            with patch("bookbrain.services.embedder.settings") as mock_settings:
                mock_settings.embedding_model = "text-embedding-3-small"
                mock_settings.embedding_batch_size = 100
                mock_settings.embedding_max_retries = 3
                mock_settings.embedding_retry_base_delay = 1.0

                result = await generate_embeddings(chunks)

                assert call_count == 1
                assert len(result.embedded_chunks) == 10
