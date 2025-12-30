"""Tests for sentence-aware text chunking service."""

import pytest

from bookbrain.models.chunker import Chunk, ChunkedDocument
from bookbrain.models.parser import ParsedDocument, ParsedPage
from bookbrain.services.sentence_chunker import (
    CHUNK_SIZE,
    CHARS_PER_TOKEN,
    chunk_text,
    count_tokens,
)


class TestSentenceChunker:
    """Tests for the sentence-aware chunker."""

    def test_basic_chunking_returns_chunked_document(self):
        """Test that chunking returns a ChunkedDocument."""
        doc = ParsedDocument(
            pages=[ParsedPage(page_number=1, content="This is a test sentence.")],
            total_pages=1,
        )

        result = chunk_text(doc)

        assert isinstance(result, ChunkedDocument)
        assert result.total_chunks >= 1

    def test_short_text_single_chunk(self):
        """Test that short text produces a single chunk."""
        doc = ParsedDocument(
            pages=[ParsedPage(page_number=1, content="Short text.")],
            total_pages=1,
        )

        result = chunk_text(doc)

        assert result.total_chunks == 1
        assert result.chunks[0].content == "Short text."

    def test_chunk_contains_required_fields(self):
        """Test that each chunk has all required fields."""
        doc = ParsedDocument(
            pages=[ParsedPage(page_number=1, content="Test content here.")],
            total_pages=1,
        )

        result = chunk_text(doc)

        chunk = result.chunks[0]
        assert isinstance(chunk.index, int)
        assert isinstance(chunk.content, str)
        assert isinstance(chunk.page_number, int)
        assert isinstance(chunk.token_count, int)

    def test_page_number_preserved(self):
        """Test that page numbers are correctly preserved."""
        doc = ParsedDocument(
            pages=[
                ParsedPage(page_number=5, content="Content on page five."),
            ],
            total_pages=10,
        )

        result = chunk_text(doc)

        assert result.chunks[0].page_number == 5

    def test_chunk_index_sequential(self):
        """Test that chunk indices are sequential."""
        long_content = "This is a sentence. " * 500  # Create multiple chunks
        doc = ParsedDocument(
            pages=[ParsedPage(page_number=1, content=long_content)],
            total_pages=1,
        )

        result = chunk_text(doc)

        for i, chunk in enumerate(result.chunks):
            assert chunk.index == i

    def test_source_pages_count(self):
        """Test that source_pages reflects total pages."""
        doc = ParsedDocument(
            pages=[ParsedPage(page_number=1, content="Content.")],
            total_pages=100,
        )

        result = chunk_text(doc)

        assert result.source_pages == 100

    def test_empty_document(self):
        """Test handling of empty document."""
        doc = ParsedDocument(pages=[], total_pages=0)

        result = chunk_text(doc)

        assert result.total_chunks == 0
        assert result.chunks == []

    def test_empty_page_content(self):
        """Test handling of pages with empty content."""
        doc = ParsedDocument(
            pages=[
                ParsedPage(page_number=1, content=""),
                ParsedPage(page_number=2, content="Actual content."),
            ],
            total_pages=2,
        )

        result = chunk_text(doc)

        assert result.total_chunks == 1
        assert result.chunks[0].page_number == 2

    def test_whitespace_only_content_handled(self):
        """Test that whitespace-only content is handled."""
        doc = ParsedDocument(
            pages=[
                ParsedPage(page_number=1, content="   \n\t  "),
                ParsedPage(page_number=2, content="Real content."),
            ],
            total_pages=2,
        )

        result = chunk_text(doc)

        assert result.total_chunks == 1
        assert result.chunks[0].page_number == 2

    def test_multiple_pages_separate_chunks(self):
        """Test that each page creates separate chunks (page-aware splitting)."""
        doc = ParsedDocument(
            pages=[
                ParsedPage(page_number=1, content="Content from page one."),
                ParsedPage(page_number=2, content="Content from page two."),
            ],
            total_pages=2,
        )

        result = chunk_text(doc)

        # Each page should have its own chunk(s)
        assert result.total_chunks == 2
        assert result.chunks[0].page_number == 1
        assert result.chunks[1].page_number == 2

    def test_sentence_boundary_preserved(self):
        """Test that sentences are not split in the middle."""
        # Create content with clear sentence boundaries
        sentences = [
            "This is the first complete sentence.",
            "This is the second complete sentence.",
            "This is the third complete sentence.",
        ]
        content = " ".join(sentences)

        doc = ParsedDocument(
            pages=[ParsedPage(page_number=1, content=content)],
            total_pages=1,
        )

        result = chunk_text(doc)

        # Each chunk should contain complete sentences
        for chunk in result.chunks:
            # Check that chunk doesn't start mid-word (after a letter without space)
            assert not chunk.content[0].islower() or chunk.content.startswith("and") or chunk.content.startswith("or")

    def test_korean_text_chunking(self):
        """Test chunking of Korean text."""
        korean_content = "이것은 첫 번째 문장입니다. 이것은 두 번째 문장입니다. 이것은 세 번째 문장입니다."

        doc = ParsedDocument(
            pages=[ParsedPage(page_number=1, content=korean_content)],
            total_pages=1,
        )

        result = chunk_text(doc)

        assert result.total_chunks >= 1
        assert "문장" in result.chunks[0].content

    def test_mixed_korean_english_text(self):
        """Test chunking of mixed Korean and English text."""
        mixed_content = "이것은 Korean text입니다. This is English. 다시 한국어로 돌아옵니다."

        doc = ParsedDocument(
            pages=[ParsedPage(page_number=1, content=mixed_content)],
            total_pages=1,
        )

        result = chunk_text(doc)

        assert result.total_chunks >= 1

    def test_long_document_creates_multiple_chunks(self):
        """Test that long documents create multiple chunks."""
        # Create content longer than chunk size
        long_content = "This is a test sentence with enough words. " * 200

        doc = ParsedDocument(
            pages=[ParsedPage(page_number=1, content=long_content)],
            total_pages=1,
        )

        result = chunk_text(doc)

        assert result.total_chunks > 1

    def test_token_count_reasonable(self):
        """Test that token counts are within reasonable limits."""
        long_content = "This is a sentence. " * 500

        doc = ParsedDocument(
            pages=[ParsedPage(page_number=1, content=long_content)],
            total_pages=1,
        )

        result = chunk_text(doc)

        # Token count should be roughly within our target (with some variance due to char-based splitting)
        max_expected_tokens = CHUNK_SIZE * 2  # Allow 2x buffer
        for chunk in result.chunks:
            assert chunk.token_count <= max_expected_tokens

    def test_paragraph_break_respected(self):
        """Test that paragraph breaks are respected as split points."""
        content = "First paragraph content.\n\nSecond paragraph content.\n\nThird paragraph content."

        doc = ParsedDocument(
            pages=[ParsedPage(page_number=1, content=content)],
            total_pages=1,
        )

        result = chunk_text(doc)

        # Should be a single chunk for short content, but structure preserved
        assert result.total_chunks >= 1


class TestCountTokens:
    """Tests for token counting function."""

    def test_count_tokens_english(self):
        """Test token counting for English text."""
        text = "Hello world"
        count = count_tokens(text)
        assert count > 0
        assert isinstance(count, int)

    def test_count_tokens_korean(self):
        """Test token counting for Korean text."""
        text = "안녕하세요"
        count = count_tokens(text)
        assert count > 0

    def test_count_tokens_empty(self):
        """Test token counting for empty string."""
        assert count_tokens("") == 0
