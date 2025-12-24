"""Embedding service for generating vector embeddings using OpenAI API."""

import asyncio

from openai import APIError, AsyncOpenAI, RateLimitError

from bookbrain.core.config import settings
from bookbrain.core.exceptions import EmbeddingError, OpenAIKeyMissingError
from bookbrain.models.chunker import Chunk
from bookbrain.models.embedder import EmbeddedChunk, EmbeddingResult

# Lazy-loaded OpenAI client
_client: AsyncOpenAI | None = None


def _get_openai_client() -> AsyncOpenAI:
    """Get or create the async OpenAI client."""
    global _client
    if _client is None:
        if not settings.openai_api_key:
            raise OpenAIKeyMissingError()
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def _call_embeddings_api(texts: list[str]) -> tuple[list[list[float]], str, int]:
    """
    Call OpenAI embeddings API with retry logic.

    Args:
        texts: List of text strings to embed

    Returns:
        Tuple of (embeddings list, model name, total tokens used)

    Raises:
        EmbeddingError: If API call fails after all retries
    """
    client = _get_openai_client()
    last_error: Exception | None = None

    for attempt in range(settings.embedding_max_retries):
        try:
            response = await client.embeddings.create(
                input=texts,
                model=settings.embedding_model,
                encoding_format="float",
            )

            embeddings = [data.embedding for data in response.data]
            return embeddings, response.model, response.usage.total_tokens

        except RateLimitError as e:
            last_error = e
            if attempt < settings.embedding_max_retries - 1:
                delay = settings.embedding_retry_base_delay * (2**attempt)
                await asyncio.sleep(delay)
            else:
                retries = settings.embedding_max_retries
                raise EmbeddingError(
                    f"Rate limit exceeded after {retries} retries", cause=e
                ) from e

        except APIError as e:
            raise EmbeddingError(f"OpenAI API error: {e}", cause=e) from e

        except Exception as e:
            raise EmbeddingError(f"Unexpected error: {e}", cause=e) from e

    # Should not reach here, but just in case
    raise EmbeddingError(
        f"Failed after {settings.embedding_max_retries} retries",
        cause=last_error,
    )


async def generate_embeddings(chunks: list[Chunk]) -> EmbeddingResult:
    """
    Generate embeddings for a list of chunks using OpenAI API.

    Processes chunks in batches to respect API rate limits.
    Uses exponential backoff for retry on rate limit errors.

    Args:
        chunks: List of Chunk objects to embed

    Returns:
        EmbeddingResult containing embedded chunks, model version, and token usage

    Raises:
        OpenAIKeyMissingError: If OpenAI API key is not configured
        EmbeddingError: If embedding generation fails
    """
    if not chunks:
        return EmbeddingResult(
            embedded_chunks=[],
            model_version=settings.embedding_model,
            total_tokens=0,
        )

    embedded_chunks: list[EmbeddedChunk] = []
    total_tokens = 0
    model_version = settings.embedding_model
    batch_size = settings.embedding_batch_size

    # Process chunks in batches
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        texts = [chunk.content for chunk in batch]

        embeddings, model, tokens = await _call_embeddings_api(texts)
        total_tokens += tokens
        model_version = model  # Use the actual model returned by API

        # Create EmbeddedChunk for each chunk in batch
        for chunk, embedding in zip(batch, embeddings):
            embedded_chunks.append(
                EmbeddedChunk(
                    chunk=chunk,
                    vector=embedding,
                )
            )

    return EmbeddingResult(
        embedded_chunks=embedded_chunks,
        model_version=model_version,
        total_tokens=total_tokens,
    )
