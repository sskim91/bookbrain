"""Search service for semantic search on indexed chunks."""

import logging
import time

from bookbrain.repositories.book_repository import get_books_by_ids
from bookbrain.repositories.vector_repository import search_similar_chunks
from bookbrain.services.embedder import generate_embedding

logger = logging.getLogger(__name__)


async def search_chunks(
    query: str,
    limit: int = 10,
    offset: int = 0,
    min_score: float | None = None,
) -> dict:
    """
    Perform semantic search on indexed chunks.

    Args:
        query: Natural language search query
        limit: Maximum number of results (default 10)
        offset: Number of results to skip (for pagination)
        min_score: Minimum similarity score threshold (0.0-1.0)

    Returns:
        dict with results, total, and query_time_ms
    """
    start_time = time.perf_counter()

    # 1. Generate query embedding
    query_embedding = await generate_embedding(query)

    # 2. Search similar chunks in Qdrant
    search_results = search_similar_chunks(
        query_embedding,
        limit=limit,
        offset=offset,
        score_threshold=min_score,
    )

    # 3. Batch fetch book metadata (N+1 query optimization)
    unique_book_ids = list({result.book_id for result in search_results})
    books_map = await get_books_by_ids(unique_book_ids)

    # 4. Enrich with book metadata
    results = []
    orphan_book_ids = []
    for result in search_results:
        book = books_map.get(result.book_id)
        if book:
            results.append(
                {
                    "book_id": result.book_id,
                    "title": book["title"],
                    "author": book["author"],
                    "page": result.page,
                    "content": result.content,
                    "score": result.score,
                }
            )
        else:
            orphan_book_ids.append(result.book_id)

    # Log warning for orphaned vectors (data integrity issue)
    if orphan_book_ids:
        unique_orphans = list(set(orphan_book_ids))
        logger.warning(
            "Orphaned vectors detected: book_ids %s not found in database. "
            "Consider running cleanup to remove stale vectors.",
            unique_orphans,
        )

    query_time_ms = (time.perf_counter() - start_time) * 1000

    return {
        "results": results,
        "total": len(results),
        "query_time_ms": round(query_time_ms, 2),
    }
