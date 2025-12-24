"""Embedder data models."""

from pydantic import BaseModel

from bookbrain.models.chunker import Chunk


class EmbeddedChunk(BaseModel):
    """Represents a chunk with its embedding vector."""

    chunk: Chunk
    vector: list[float]


class EmbeddingResult(BaseModel):
    """Result of embedding generation for a document."""

    embedded_chunks: list[EmbeddedChunk]
    model_version: str
    total_tokens: int
