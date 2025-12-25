"""Search API routes."""

from fastapi import APIRouter, HTTPException

from bookbrain.core.exceptions import EmbeddingError
from bookbrain.models.schemas import SearchRequest, SearchResponse
from bookbrain.services.searcher import search_chunks

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    """
    Perform semantic search on indexed books.

    Returns top matching chunks sorted by similarity score.
    """
    try:
        result = await search_chunks(
            query=request.query,
            limit=request.limit,
            offset=request.offset,
            min_score=request.min_score,
        )
        return SearchResponse(**result)
    except EmbeddingError as e:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "EMBEDDING_FAILED", "message": str(e)}},
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "SEARCH_FAILED", "message": str(e)}},
        ) from e
