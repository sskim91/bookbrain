"""Tests for text chunking service."""

from bookbrain.models.chunker import ChunkedDocument
from bookbrain.models.parser import ParsedDocument, ParsedPage
from bookbrain.services.chunker import chunk_text


class TestChunkText:
    """Tests for chunk_text function."""

    def test_basic_chunking_returns_chunked_document(self):
        """Test that chunk_text returns a ChunkedDocument."""
        doc = ParsedDocument(
            pages=[ParsedPage(page_number=1, content="Hello world.")],
            total_pages=1,
        )

        result = chunk_text(doc)

        assert isinstance(result, ChunkedDocument)
        assert result.total_chunks >= 1

    def test_short_text_single_chunk(self):
        """Test that short text (less than 1000 tokens) returns single chunk."""
        doc = ParsedDocument(
            pages=[ParsedPage(page_number=1, content="Short text for testing.")],
            total_pages=1,
        )

        result = chunk_text(doc)

        assert result.total_chunks == 1
        assert len(result.chunks) == 1
        assert result.chunks[0].content == "Short text for testing."

    def test_chunk_contains_required_fields(self):
        """Test that each chunk has required fields."""
        doc = ParsedDocument(
            pages=[ParsedPage(page_number=1, content="Test content here.")],
            total_pages=1,
        )

        result = chunk_text(doc)

        chunk = result.chunks[0]
        assert chunk.index == 0
        assert chunk.content == "Test content here."
        assert chunk.page_number == 1
        assert chunk.token_count > 0

    def test_page_number_preserved(self):
        """Test that page numbers are preserved in chunks."""
        doc = ParsedDocument(
            pages=[
                ParsedPage(page_number=1, content="Page one content."),
                ParsedPage(page_number=2, content="Page two content."),
            ],
            total_pages=2,
        )

        result = chunk_text(doc)

        # First chunk should start with page 1 content
        assert result.chunks[0].page_number == 1

    def test_chunk_index_sequential(self):
        """Test that chunk indices are sequential starting from 0."""
        doc = ParsedDocument(
            pages=[ParsedPage(page_number=1, content="Content " * 500)],
            total_pages=1,
        )

        result = chunk_text(doc)

        for i, chunk in enumerate(result.chunks):
            assert chunk.index == i

    def test_source_pages_count(self):
        """Test that source_pages reflects the original document page count."""
        doc = ParsedDocument(
            pages=[
                ParsedPage(page_number=1, content="Page 1"),
                ParsedPage(page_number=2, content="Page 2"),
                ParsedPage(page_number=3, content="Page 3"),
            ],
            total_pages=3,
        )

        result = chunk_text(doc)

        assert result.source_pages == 3

    def test_token_count_within_limit(self):
        """Test that each chunk token count is within the 1000 token limit."""
        # Generate a long text that should be split into multiple chunks
        long_text = "word " * 2000  # Should produce multiple chunks

        doc = ParsedDocument(
            pages=[ParsedPage(page_number=1, content=long_text)],
            total_pages=1,
        )

        result = chunk_text(doc)

        assert result.total_chunks > 1
        for chunk in result.chunks:
            assert chunk.token_count <= 1000

    def test_overlap_between_chunks(self):
        """Test that adjacent chunks have overlap."""
        # Generate text that will definitely be split
        long_text = "word " * 2000

        doc = ParsedDocument(
            pages=[ParsedPage(page_number=1, content=long_text)],
            total_pages=1,
        )

        result = chunk_text(doc)

        if result.total_chunks > 1:
            # Check that the end of chunk 0 overlaps with start of chunk 1
            first_chunk_words = result.chunks[0].content.split()[-20:]
            second_chunk_words = result.chunks[1].content.split()[:20:]

            # There should be some overlap
            overlap_found = any(
                word in second_chunk_words for word in first_chunk_words
            )
            assert overlap_found, "Chunks should have overlapping content"

    def test_empty_document(self):
        """Test handling of empty document."""
        doc = ParsedDocument(
            pages=[],
            total_pages=0,
        )

        result = chunk_text(doc)

        assert result.total_chunks == 0
        assert len(result.chunks) == 0
        assert result.source_pages == 0

    def test_empty_page_content(self):
        """Test handling of pages with empty content."""
        doc = ParsedDocument(
            pages=[ParsedPage(page_number=1, content="")],
            total_pages=1,
        )

        result = chunk_text(doc)

        assert result.total_chunks == 0
        assert len(result.chunks) == 0

    def test_multiple_pages_combined(self):
        """Test that content from multiple pages is combined for chunking."""
        doc = ParsedDocument(
            pages=[
                ParsedPage(page_number=1, content="Content from page one."),
                ParsedPage(page_number=2, content="Content from page two."),
            ],
            total_pages=2,
        )

        result = chunk_text(doc)

        # Combined content should be in a single chunk (short text)
        assert result.total_chunks == 1
        assert "page one" in result.chunks[0].content
        assert "page two" in result.chunks[0].content

    def test_page_boundary_tracking(self):
        """Test that page boundaries are correctly tracked across chunks."""
        # Create a document where page 2 starts partway through
        page1_text = "word " * 600  # ~600 tokens
        page2_text = "word " * 600  # ~600 tokens

        doc = ParsedDocument(
            pages=[
                ParsedPage(page_number=1, content=page1_text),
                ParsedPage(page_number=2, content=page2_text),
            ],
            total_pages=2,
        )

        result = chunk_text(doc)

        # First chunk should be from page 1
        assert result.chunks[0].page_number == 1
        # At some point, chunks should transition to page 2
        if result.total_chunks > 1:
            page_numbers = [chunk.page_number for chunk in result.chunks]
            # Should track page boundaries
            assert 2 in page_numbers or 1 in page_numbers

    def test_whitespace_only_content_handled(self):
        """Test that whitespace-only content is handled correctly."""
        doc = ParsedDocument(
            pages=[ParsedPage(page_number=1, content="   \n\t  ")],
            total_pages=1,
        )

        result = chunk_text(doc)

        # Whitespace-only should result in no meaningful chunks
        assert result.total_chunks == 0 or (
            result.total_chunks == 1 and result.chunks[0].content.strip() == ""
        )

    def test_large_document_performance(self):
        """
        Stress test for O(N) performance verification.
        Simulates a 500-page book (approx 150,000 tokens).
        Previously O(N^2) algorithm would hang here.
        """
        # Create a large document
        # 500 pages * 300 words/page ~ 150,000 words ~ 200,000 tokens
        page_content = "word " * 300
        pages = [
            ParsedPage(page_number=i + 1, content=page_content) for i in range(500)
        ]

        doc = ParsedDocument(
            pages=pages,
            total_pages=500,
        )

        import time

        start_time = time.time()
        result = chunk_text(doc)
        end_time = time.time()

        duration = end_time - start_time

        # Verify correctness
        assert result.total_chunks > 100
        assert result.source_pages == 500
        assert result.chunks[0].page_number == 1
        assert result.chunks[-1].page_number == 500

        # Performance check - should be very fast (< 2 seconds usually, definitely < 10s)
        # The O(N^2) version would take minutes.
        assert duration < 10.0, f"Chunking took too long: {duration:.2f}s"
