"""Sentence-aware text chunking service using LangChain RecursiveCharacterTextSplitter.

This is an alternative to the token-based chunker.py that splits at natural
sentence boundaries to avoid cutting sentences in the middle.

Usage:
    from bookbrain.services.sentence_chunker import chunk_text
    # or to use both:
    from bookbrain.services import chunker  # token-based (original)
    from bookbrain.services import sentence_chunker  # sentence-aware (new)
"""

import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter

from bookbrain.models.chunker import Chunk, ChunkedDocument
from bookbrain.models.parser import ParsedDocument

# Constants for chunking configuration
CHUNK_SIZE = 300  # target tokens (converted to ~1200 characters)
CHUNK_OVERLAP = 50  # overlap in characters
CHARS_PER_TOKEN = 4  # approximate ratio for Korean/English mixed text

# Separators prioritized for sentence-aware splitting
# Korean sentence endings (。) + English sentence endings + paragraph breaks
SEPARATORS = [
    "\n\n",  # Paragraph break (highest priority)
    "\n",    # Line break
    "。",    # Korean period (full-width)
    ". ",    # English sentence end
    "! ",    # Exclamation
    "? ",    # Question
    ".\n",   # Period + newline
    "!\n",   # Exclamation + newline
    "?\n",   # Question + newline
    ";",     # Semicolon
    ":",     # Colon
    " ",     # Space (last resort)
    "",      # Character (final fallback)
]

# Lazy-loaded encoding cache
_encoding = None


def _get_encoding():
    """Get or create the tiktoken encoding."""
    global _encoding
    if _encoding is None:
        _encoding = tiktoken.get_encoding("cl100k_base")
    return _encoding


def count_tokens(text: str) -> int:
    """Count the number of tokens in a text string."""
    return len(_get_encoding().encode(text))


def chunk_text(parsed_document: ParsedDocument) -> ChunkedDocument:
    """
    Split a ParsedDocument into sentence-aware chunks.

    Uses RecursiveCharacterTextSplitter to split at natural boundaries
    (paragraphs, sentences) rather than arbitrary token counts.
    Each page is processed separately to maintain accurate page tracking.

    Args:
        parsed_document: A ParsedDocument containing pages of text.

    Returns:
        ChunkedDocument containing the chunks with preserved page information.
    """
    if not parsed_document.pages:
        return ChunkedDocument(
            chunks=[],
            total_chunks=0,
            source_pages=parsed_document.total_pages,
        )

    # Build page content list
    page_contents: list[tuple[int, str]] = []
    for page in parsed_document.pages:
        if page.content and page.content.strip():
            page_contents.append((page.page_number, page.content))

    if not page_contents:
        return ChunkedDocument(
            chunks=[],
            total_chunks=0,
            source_pages=parsed_document.total_pages,
        )

    # Create text splitter with sentence-aware separators
    chunk_size_chars = CHUNK_SIZE * CHARS_PER_TOKEN

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size_chars,
        chunk_overlap=CHUNK_OVERLAP,
        separators=SEPARATORS,
        keep_separator=True,
        length_function=len,
    )

    # Process each page and create chunks
    chunks: list[Chunk] = []
    chunk_index = 0

    for page_number, content in page_contents:
        # Split this page's content
        page_chunks = splitter.split_text(content)

        for chunk_content in page_chunks:
            chunk_content = chunk_content.strip()
            if not chunk_content:
                continue

            chunk = Chunk(
                index=chunk_index,
                content=chunk_content,
                page_number=page_number,
                token_count=count_tokens(chunk_content),
            )
            chunks.append(chunk)
            chunk_index += 1

    return ChunkedDocument(
        chunks=chunks,
        total_chunks=len(chunks),
        source_pages=parsed_document.total_pages,
    )


# Utility functions (same as original chunker for compatibility)
def tokenize(text: str) -> list[int]:
    """Convert text to a list of token IDs."""
    return _get_encoding().encode(text)


def detokenize(tokens: list[int]) -> str:
    """Convert token IDs back to text."""
    return _get_encoding().decode(tokens)
