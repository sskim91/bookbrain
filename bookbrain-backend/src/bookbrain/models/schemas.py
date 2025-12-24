"""API request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


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
