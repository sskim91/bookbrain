"""Qdrant vector database connection and utilities."""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from bookbrain.core.config import settings


def get_qdrant_client() -> QdrantClient:
    """Create a Qdrant client instance."""
    return QdrantClient(url=settings.qdrant_url)


def ensure_collection_exists(client: QdrantClient | None = None) -> bool:
    """
    Ensure the chunks collection exists, creating it if necessary.

    Returns:
        True if collection was created, False if it already existed.
    """
    if client is None:
        client = get_qdrant_client()

    collection_name = settings.qdrant_collection

    # Check if collection exists
    collections = client.get_collections().collections
    exists = any(c.name == collection_name for c in collections)

    if not exists:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=settings.vector_size,
                distance=Distance.COSINE,
            ),
        )
        return True

    return False


def delete_collection(client: QdrantClient | None = None) -> bool:
    """
    Delete the chunks collection if it exists.

    Returns:
        True if collection was deleted, False if it didn't exist.
    """
    if client is None:
        client = get_qdrant_client()

    collection_name = settings.qdrant_collection

    # Check if collection exists
    collections = client.get_collections().collections
    exists = any(c.name == collection_name for c in collections)

    if exists:
        client.delete_collection(collection_name=collection_name)
        return True

    return False
