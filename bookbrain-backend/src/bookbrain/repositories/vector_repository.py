"""Repository for vector storage operations in Qdrant."""

from dataclasses import dataclass
from typing import TypedDict
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue, PointStruct

from bookbrain.core.config import settings
from bookbrain.core.vector_db import get_qdrant_client


class ChunkPayload(TypedDict):
    """Type-safe payload structure for Qdrant chunks."""

    book_id: int
    page: int
    content: str
    model_version: str


@dataclass
class ChunkData:
    """Data structure for a chunk to be stored."""

    vector: list[float]
    book_id: int
    page: int
    content: str
    model_version: str

    def to_payload(self) -> ChunkPayload:
        """Convert to Qdrant payload."""
        return ChunkPayload(
            book_id=self.book_id,
            page=self.page,
            content=self.content,
            model_version=self.model_version,
        )


def store_chunks(
    chunks: list[ChunkData],
    client: QdrantClient | None = None,
) -> int:
    """
    Store chunks with their vectors in Qdrant.

    Args:
        chunks: List of ChunkData objects containing vectors and metadata
        client: Optional Qdrant client (creates new one if not provided)

    Returns:
        Number of chunks stored

    Warning:
        This function does NOT verify that book_id exists in PostgreSQL.
        Callers should ensure book_id validity before calling this function
        to prevent orphaned vectors.

    TODO: Consider adding book_id validation or moving this responsibility
          to a service layer that coordinates between PostgreSQL and Qdrant.
    """
    if not chunks:
        return 0

    if client is None:
        client = get_qdrant_client()

    points = [
        PointStruct(
            id=str(uuid4()),
            vector=chunk.vector,
            payload=chunk.to_payload(),
        )
        for chunk in chunks
    ]

    client.upsert(
        collection_name=settings.qdrant_collection,
        points=points,
        wait=True,
    )

    return len(points)


def delete_chunks_by_book_id(
    book_id: int,
    client: QdrantClient | None = None,
) -> bool:
    """
    Delete all chunks associated with a book.

    Args:
        book_id: The book ID whose chunks should be deleted
        client: Optional Qdrant client (creates new one if not provided)

    Returns:
        True if deletion was successful
    """
    if client is None:
        client = get_qdrant_client()

    client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="book_id",
                    match=MatchValue(value=book_id),
                )
            ]
        ),
        wait=True,
    )

    return True


def get_chunks_by_book_id(
    book_id: int,
    client: QdrantClient | None = None,
    limit: int = 100,
) -> list[dict]:
    """
    Get all chunks for a specific book.

    Args:
        book_id: The book ID
        client: Optional Qdrant client
        limit: Maximum number of chunks to return

    Returns:
        List of chunk payloads
    """
    if client is None:
        client = get_qdrant_client()

    results = client.scroll(
        collection_name=settings.qdrant_collection,
        scroll_filter=Filter(
            must=[
                FieldCondition(
                    key="book_id",
                    match=MatchValue(value=book_id),
                )
            ]
        ),
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )

    points, _ = results
    return [point.payload for point in points if point.payload]
