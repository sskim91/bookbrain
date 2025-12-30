"""Services for BookBrain."""

from bookbrain.services.sentence_chunker import chunk_text  # sentence-aware chunking
from bookbrain.services.embedder import generate_embeddings
from bookbrain.services.indexer import IndexingResult, index_book
from bookbrain.services.parser import parse_pdf

__all__ = [
    "chunk_text",
    "generate_embeddings",
    "index_book",
    "IndexingResult",
    "parse_pdf",
]
