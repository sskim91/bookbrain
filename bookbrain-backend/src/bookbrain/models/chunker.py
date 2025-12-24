"""Chunker data models."""

from pydantic import BaseModel


class Chunk(BaseModel):
    """Represents a single text chunk from a parsed document."""

    index: int
    content: str
    page_number: int
    token_count: int


class ChunkedDocument(BaseModel):
    """Represents a document that has been split into chunks."""

    chunks: list[Chunk]
    total_chunks: int
    source_pages: int
