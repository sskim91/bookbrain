"""API request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BookBase(BaseModel):
    """Base book schema."""

    title: str
    author: str | None = None


class BookResponse(BaseModel):
    """Single book response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str | None
    file_path: str
    total_pages: int | None
    embedding_model: str | None
    created_at: datetime


class BookListResponse(BaseModel):
    """Book list response."""

    books: list[BookResponse]
    total: int


class IndexingResponse(BaseModel):
    """Indexing result response."""

    status: str  # "indexed"
    book_id: int
    chunks_count: int


class ErrorDetail(BaseModel):
    """Error detail structure."""

    code: str
    message: str
    details: dict = {}


class ErrorResponse(BaseModel):
    """Error response wrapper."""

    error: ErrorDetail


class DeleteResponse(BaseModel):
    """Delete operation response."""

    deleted: bool


# Search schemas (Story 2.1)
class SearchRequest(BaseModel):
    """Search request schema."""

    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=10, ge=1, le=50)
    offset: int = Field(default=0, ge=0)
    min_score: float | None = Field(default=None, ge=0.0, le=1.0)


class SearchResultItem(BaseModel):
    """Single search result item."""

    book_id: int
    title: str
    author: str | None
    page: int
    content: str
    score: float  # 0.0 ~ 1.0 (Qdrant similarity score)


class SearchResponse(BaseModel):
    """Search response schema."""

    results: list[SearchResultItem]
    total: int
    query_time_ms: float
