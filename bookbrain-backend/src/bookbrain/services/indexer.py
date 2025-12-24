"""Indexer service for the book indexing pipeline."""

import logging

from pydantic import BaseModel

from bookbrain.core.exceptions import IndexingError
from bookbrain.models.chunker import ChunkedDocument
from bookbrain.repositories.book_repository import update_book_embedding_model
from bookbrain.repositories.vector_repository import (
    ChunkData,
    delete_chunks_by_book_id,
    store_chunks,
)
from bookbrain.services.embedder import generate_embeddings

logger = logging.getLogger(__name__)


class IndexingResult(BaseModel):
    """Result of book indexing operation."""

    book_id: int
    chunks_stored: int
    model_version: str
    total_tokens: int


async def index_book(
    book_id: int,
    chunked_document: ChunkedDocument,
) -> IndexingResult:
    """
    Index a book by generating embeddings and storing them in Qdrant.

    This function orchestrates the full indexing pipeline:
    1. Generate embeddings for all chunks using OpenAI API
    2. Store vectors in Qdrant with metadata
    3. Update the book's embedding_model in PostgreSQL

    Args:
        book_id: The ID of the book to index
        chunked_document: The chunked document to index

    Returns:
        IndexingResult containing the number of chunks stored and model info

    Raises:
        IndexingError: If indexing fails at any step
        EmbeddingError: If embedding generation fails
        OpenAIKeyMissingError: If OpenAI API key is not configured
    """
    if not chunked_document.chunks:
        # Nothing to index
        return IndexingResult(
            book_id=book_id,
            chunks_stored=0,
            model_version="",
            total_tokens=0,
        )

    try:
        # Step 1: Generate embeddings
        embedding_result = await generate_embeddings(chunked_document.chunks)

        # Step 2: Prepare data for Qdrant
        chunk_data_list = [
            ChunkData(
                vector=ec.vector,
                book_id=book_id,
                page=ec.chunk.page_number,
                content=ec.chunk.content,
                model_version=embedding_result.model_version,
            )
            for ec in embedding_result.embedded_chunks
        ]

        # Step 3: Store in Qdrant
        chunks_stored = store_chunks(chunk_data_list)

        # Step 4: Update book's embedding_model in PostgreSQL
        await update_book_embedding_model(
            book_id=book_id,
            embedding_model=embedding_result.model_version,
            total_pages=chunked_document.source_pages,
        )

        return IndexingResult(
            book_id=book_id,
            chunks_stored=chunks_stored,
            model_version=embedding_result.model_version,
            total_tokens=embedding_result.total_tokens,
        )

    except Exception as e:
        # Rollback: Delete any chunks that may have been stored
        try:
            delete_chunks_by_book_id(book_id)
        except Exception as cleanup_error:
            logger.error(
                f"Failed to rollback (delete chunks) for book {book_id}: {cleanup_error}"
            )

        if isinstance(e, IndexingError):
            raise

        raise IndexingError(f"Failed to index book {book_id}: {e}", cause=e) from e
