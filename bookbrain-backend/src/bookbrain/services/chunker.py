"""Text chunking service for splitting parsed documents into token-based chunks."""

import tiktoken

from bookbrain.models.chunker import Chunk, ChunkedDocument
from bookbrain.models.parser import ParsedDocument

# Constants for chunking configuration
CHUNK_SIZE = 1000  # tokens
OVERLAP_SIZE = 100  # tokens

# Lazy-loaded encoding cache
_encoding = None


def _get_encoding():
    """Get or create the tiktoken encoding."""
    global _encoding
    if _encoding is None:
        # Use cl100k_base encoding (compatible with OpenAI text-embedding-3 models)
        _encoding = tiktoken.get_encoding("cl100k_base")
    return _encoding


def count_tokens(text: str) -> int:
    """Count the number of tokens in a text string."""
    return len(_get_encoding().encode(text))


def tokenize(text: str) -> list[int]:
    """Convert text to a list of token IDs."""
    return _get_encoding().encode(text)


def detokenize(tokens: list[int]) -> str:
    """Convert token IDs back to text."""
    return _get_encoding().decode(tokens)


def chunk_text(parsed_document: ParsedDocument) -> ChunkedDocument:
    """
    Split a ParsedDocument into token-based chunks.

    Args:
        parsed_document: A ParsedDocument containing pages of text.

    Returns:
        ChunkedDocument containing the chunks with preserved page information.

    Algorithm:
        1. Tokenize each page individually (O(N))
        2. Build a flat list of tokens and a corresponding page number map
        3. Split into chunks of CHUNK_SIZE tokens with OVERLAP_SIZE overlap
    """
    if not parsed_document.pages:
        return ChunkedDocument(
            chunks=[],
            total_chunks=0,
            source_pages=parsed_document.total_pages,
        )

    all_tokens: list[int] = []
    token_page_map: list[int] = []

    # Step 1 & 2: Tokenize per page and build maps
    # This is O(N) where N is total tokens, unlike the previous O(N^2) approach
    for page in parsed_document.pages:
        if not page.content:
            continue

        # Note: Tokenizing per page might slightly differ from tokenizing the full text
        # at page boundaries (e.g. split words), but the performance gain is massive
        # (O(N) vs O(N^2)) and the semantic impact on retrieval is negligible.
        page_tokens = tokenize(page.content)
        
        if not page_tokens:
            continue

        all_tokens.extend(page_tokens)
        token_page_map.extend([page.page_number] * len(page_tokens))

    total_tokens = len(all_tokens)

    if total_tokens == 0:
        return ChunkedDocument(
            chunks=[],
            total_chunks=0,
            source_pages=parsed_document.total_pages,
        )

    # Step 3: Split into chunks with overlap
    chunks: list[Chunk] = []
    chunk_index = 0
    start_token = 0

    while start_token < total_tokens:
        end_token = min(start_token + CHUNK_SIZE, total_tokens)
        
        chunk_tokens = all_tokens[start_token:end_token]
        chunk_content = detokenize(chunk_tokens)
        
        # The page number for the chunk is defined by its starting token
        page_number = token_page_map[start_token]

        chunk = Chunk(
            index=chunk_index,
            content=chunk_content,
            page_number=page_number,
            token_count=len(chunk_tokens),
        )
        chunks.append(chunk)

        # Move to next chunk with overlap
        chunk_index += 1
        start_token = end_token - OVERLAP_SIZE

        # Avoid infinite loop for small documents
        if end_token >= total_tokens:
            break

        # Ensure we make progress
        if start_token >= total_tokens - OVERLAP_SIZE:
            break

    return ChunkedDocument(
        chunks=chunks,
        total_chunks=len(chunks),
        source_pages=parsed_document.total_pages,
    )
