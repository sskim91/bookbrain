"""Parser data models."""

from pydantic import BaseModel


class ParsedPage(BaseModel):
    """Represents a single parsed page from a PDF document."""

    page_number: int
    content: str
    tables: list[dict] = []
    figures: list[dict] = []


class ParsedDocument(BaseModel):
    """Represents a fully parsed PDF document."""

    pages: list[ParsedPage]
    total_pages: int
    metadata: dict | None = None
