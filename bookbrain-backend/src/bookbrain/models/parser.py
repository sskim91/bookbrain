"""Parser data models."""

from typing import Any

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


class ParseResult(BaseModel):
    """Result of parsing a PDF, including raw API response for storage."""

    document: ParsedDocument
    raw_response: dict[str, Any]
