"""Repository for vector storage operations in Qdrant."""

from dataclasses import dataclass
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue, PointStruct

from bookbrain.core.config import settings
from bookbrain.core.vector_db import get_qdrant_client


@dataclass
class ChunkData:
    """Data structure for a chunk to be stored."""

    vector: list[float]
    book_id: int
    page: int
    content: str
    model_version: str


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
    """
    if not chunks:
        return 0

    if client is None:
        client = get_qdrant_client()

    points = [
        PointStruct(
            id=str(uuid4()),
            vector=chunk.vector,
            payload={
                "book_id": chunk.book_id,
                "page": chunk.page,
                "content": chunk.content,
                "model_version": chunk.model_version,
            },
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
