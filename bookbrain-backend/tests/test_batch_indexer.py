"""Tests for batch_indexer service."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add scripts directory to path for CLI tests
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from bookbrain.core.exceptions import (
    DuplicateBookError,
    IndexingError,
    InvalidFileFormatError,
    PDFReadError,
)
from bookbrain.services.batch_indexer import (
    BatchIndexingResult,
    copy_to_local_storage,
    index_local_pdf,
    validate_pdf_file_path,
)


class TestValidatePdfFilePath:
    """Tests for validate_pdf_file_path function."""

    def test_valid_pdf_file(self, tmp_path: Path):
        """Valid PDF file should pass validation."""
        pdf_file = tmp_path / "test.pdf"
        # Write valid PDF magic number
        pdf_file.write_bytes(b"%PDF-1.4\n")

        # Should not raise
        validate_pdf_file_path(pdf_file)

    def test_file_not_found(self, tmp_path: Path):
        """Non-existent file should raise PDFReadError."""
        pdf_file = tmp_path / "nonexistent.pdf"

        with pytest.raises(PDFReadError):
            validate_pdf_file_path(pdf_file)

    def test_directory_instead_of_file(self, tmp_path: Path):
        """Directory should raise PDFReadError."""
        with pytest.raises(PDFReadError):
            validate_pdf_file_path(tmp_path)

    def test_wrong_extension(self, tmp_path: Path):
        """Non-PDF extension should raise InvalidFileFormatError."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_bytes(b"%PDF-1.4\n")  # Valid header but wrong extension

        with pytest.raises(InvalidFileFormatError):
            validate_pdf_file_path(txt_file)

    def test_invalid_magic_number(self, tmp_path: Path):
        """File without PDF magic number should raise InvalidFileFormatError."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"Not a PDF file\n")

        with pytest.raises(InvalidFileFormatError):
            validate_pdf_file_path(pdf_file)

    def test_empty_file(self, tmp_path: Path):
        """Empty file should raise InvalidFileFormatError."""
        pdf_file = tmp_path / "empty.pdf"
        pdf_file.write_bytes(b"")

        with pytest.raises(InvalidFileFormatError):
            validate_pdf_file_path(pdf_file)


class TestCopyToLocalStorage:
    """Tests for copy_to_local_storage function."""

    def test_copy_file_success(self, tmp_path: Path):
        """File should be copied to storage directory."""
        # Create source file
        source_file = tmp_path / "source" / "test.pdf"
        source_file.parent.mkdir(parents=True)
        source_file.write_bytes(b"%PDF-1.4\ntest content")

        # Create storage dir
        storage_dir = tmp_path / "storage"

        with patch("bookbrain.services.batch_indexer.settings") as mock_settings:
            mock_settings.pdf_storage_dir = str(storage_dir)

            result = copy_to_local_storage(source_file)

            # Check file was copied
            assert Path(result).exists()
            assert Path(result).read_bytes() == source_file.read_bytes()
            assert Path(result).parent == storage_dir


class TestIndexLocalPdf:
    """Tests for index_local_pdf function."""

    @pytest.fixture
    def mock_dependencies(self, tmp_path: Path):
        """Mock all external dependencies for index_local_pdf."""
        # Create a valid PDF file
        pdf_file = tmp_path / "test_book.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\ntest content")

        # Mock parse result
        mock_parse_result = MagicMock()
        mock_parse_result.document = MagicMock()
        mock_parse_result.raw_response = {"jobId": "test-job"}

        # Mock chunked document
        mock_chunked_doc = MagicMock()

        # Mock indexing result
        mock_indexing_result = MagicMock()
        mock_indexing_result.chunks_stored = 10

        return {
            "pdf_file": pdf_file,
            "parse_result": mock_parse_result,
            "chunked_doc": mock_chunked_doc,
            "indexing_result": mock_indexing_result,
        }

    @pytest.mark.asyncio
    async def test_index_local_pdf_success_local_storage(
        self, tmp_path: Path, mock_dependencies
    ):
        """Successfully index a PDF with local storage."""
        storage_dir = tmp_path / "storage"

        with (
            patch(
                "bookbrain.services.batch_indexer.parse_pdf",
                new_callable=AsyncMock,
                return_value=mock_dependencies["parse_result"],
            ),
            patch(
                "bookbrain.services.batch_indexer.chunk_text",
                return_value=mock_dependencies["chunked_doc"],
            ),
            patch(
                "bookbrain.services.batch_indexer.index_book",
                new_callable=AsyncMock,
                return_value=mock_dependencies["indexing_result"],
            ),
            patch(
                "bookbrain.services.batch_indexer.book_repository"
            ) as mock_book_repo,
            patch("bookbrain.services.batch_indexer.settings") as mock_settings,
        ):
            mock_settings.s3_enabled = False
            mock_settings.pdf_storage_dir = str(storage_dir)
            mock_book_repo.create_book = AsyncMock(return_value=123)
            mock_book_repo.exists_by_title = AsyncMock(return_value=False)

            result = await index_local_pdf(mock_dependencies["pdf_file"])

            assert isinstance(result, BatchIndexingResult)
            assert result.book_id == 123
            assert result.title == "test_book"
            assert result.chunks_count == 10
            assert result.status == "indexed"

    @pytest.mark.asyncio
    async def test_index_local_pdf_success_s3_storage(
        self, tmp_path: Path, mock_dependencies
    ):
        """Successfully index a PDF with S3 storage."""
        with (
            patch(
                "bookbrain.services.batch_indexer.parse_pdf",
                new_callable=AsyncMock,
                return_value=mock_dependencies["parse_result"],
            ),
            patch(
                "bookbrain.services.batch_indexer.chunk_text",
                return_value=mock_dependencies["chunked_doc"],
            ),
            patch(
                "bookbrain.services.batch_indexer.index_book",
                new_callable=AsyncMock,
                return_value=mock_dependencies["indexing_result"],
            ),
            patch(
                "bookbrain.services.batch_indexer.book_repository"
            ) as mock_book_repo,
            patch("bookbrain.services.batch_indexer.settings") as mock_settings,
            patch(
                "bookbrain.services.batch_indexer.upload_temp_to_s3",
                return_value="s3://bucket/pdfs/uuid.pdf",
            ),
            patch(
                "bookbrain.services.batch_indexer.save_parsed_result_to_s3",
                return_value="s3://bucket/parsed/123.json",
            ),
        ):
            mock_settings.s3_enabled = True
            mock_book_repo.create_book = AsyncMock(return_value=123)
            mock_book_repo.exists_by_title = AsyncMock(return_value=False)

            result = await index_local_pdf(
                mock_dependencies["pdf_file"],
                title="Custom Title",
                author="Test Author",
            )

            assert result.book_id == 123
            assert result.title == "Custom Title"
            mock_book_repo.create_book.assert_called_once_with(
                title="Custom Title",
                file_path="s3://bucket/pdfs/uuid.pdf",
                author="Test Author",
            )

    @pytest.mark.asyncio
    async def test_index_local_pdf_invalid_file(self, tmp_path: Path):
        """Invalid file should raise InvalidFileFormatError."""
        invalid_file = tmp_path / "not_a_pdf.pdf"
        invalid_file.write_bytes(b"Not a PDF")

        with pytest.raises(InvalidFileFormatError):
            await index_local_pdf(invalid_file)

    @pytest.mark.asyncio
    async def test_index_local_pdf_file_not_found(self, tmp_path: Path):
        """Non-existent file should raise PDFReadError."""
        missing_file = tmp_path / "missing.pdf"

        with pytest.raises(PDFReadError):
            await index_local_pdf(missing_file)

    @pytest.mark.asyncio
    async def test_index_local_pdf_duplicate_book(
        self, tmp_path: Path, mock_dependencies
    ):
        """Duplicate book should raise DuplicateBookError when skip_existing=False."""
        storage_dir = tmp_path / "storage"

        with (
            patch(
                "bookbrain.services.batch_indexer.parse_pdf",
                new_callable=AsyncMock,
                return_value=mock_dependencies["parse_result"],
            ),
            patch(
                "bookbrain.services.batch_indexer.book_repository"
            ) as mock_book_repo,
            patch("bookbrain.services.batch_indexer.settings") as mock_settings,
        ):
            mock_settings.s3_enabled = False
            mock_settings.pdf_storage_dir = str(storage_dir)
            mock_book_repo.create_book = AsyncMock(
                side_effect=DuplicateBookError("test.pdf")
            )
            # skip_existing=False means we don't check before create

            with pytest.raises(DuplicateBookError):
                await index_local_pdf(mock_dependencies["pdf_file"], skip_existing=False)

    @pytest.mark.asyncio
    async def test_index_local_pdf_indexing_error_cleanup(
        self, tmp_path: Path, mock_dependencies
    ):
        """IndexingError should trigger cleanup."""
        storage_dir = tmp_path / "storage"

        with (
            patch(
                "bookbrain.services.batch_indexer.parse_pdf",
                new_callable=AsyncMock,
                return_value=mock_dependencies["parse_result"],
            ),
            patch(
                "bookbrain.services.batch_indexer.chunk_text",
                return_value=mock_dependencies["chunked_doc"],
            ),
            patch(
                "bookbrain.services.batch_indexer.index_book",
                new_callable=AsyncMock,
                side_effect=IndexingError("Embedding failed"),
            ),
            patch(
                "bookbrain.services.batch_indexer.book_repository"
            ) as mock_book_repo,
            patch("bookbrain.services.batch_indexer.settings") as mock_settings,
            patch(
                "bookbrain.services.batch_indexer.delete_stored_file"
            ) as mock_delete_file,
        ):
            mock_settings.s3_enabled = False
            mock_settings.pdf_storage_dir = str(storage_dir)
            mock_book_repo.create_book = AsyncMock(return_value=123)
            mock_book_repo.delete_book = AsyncMock()
            mock_book_repo.exists_by_title = AsyncMock(return_value=False)

            with pytest.raises(IndexingError):
                await index_local_pdf(mock_dependencies["pdf_file"])

            # Verify cleanup was called
            mock_book_repo.delete_book.assert_called_once_with(123)
            mock_delete_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_index_local_pdf_skip_existing(
        self, tmp_path: Path, mock_dependencies
    ):
        """Existing book should be skipped when skip_existing=True."""
        with (
            patch(
                "bookbrain.services.batch_indexer.book_repository"
            ) as mock_book_repo,
        ):
            mock_book_repo.exists_by_title = AsyncMock(return_value=True)

            result = await index_local_pdf(
                mock_dependencies["pdf_file"], skip_existing=True
            )

            assert result.skipped is True
            assert result.status == "skipped"
            assert "already exists" in result.skip_reason
            assert result.book_id is None

    @pytest.mark.asyncio
    async def test_index_local_pdf_no_skip_existing(
        self, tmp_path: Path, mock_dependencies
    ):
        """When skip_existing=False, duplicate check is not performed."""
        storage_dir = tmp_path / "storage"

        with (
            patch(
                "bookbrain.services.batch_indexer.parse_pdf",
                new_callable=AsyncMock,
                return_value=mock_dependencies["parse_result"],
            ),
            patch(
                "bookbrain.services.batch_indexer.chunk_text",
                return_value=mock_dependencies["chunked_doc"],
            ),
            patch(
                "bookbrain.services.batch_indexer.index_book",
                new_callable=AsyncMock,
                return_value=mock_dependencies["indexing_result"],
            ),
            patch(
                "bookbrain.services.batch_indexer.book_repository"
            ) as mock_book_repo,
            patch("bookbrain.services.batch_indexer.settings") as mock_settings,
        ):
            mock_settings.s3_enabled = False
            mock_settings.pdf_storage_dir = str(storage_dir)
            mock_book_repo.create_book = AsyncMock(return_value=123)
            # exists_by_title should NOT be called when skip_existing=False

            result = await index_local_pdf(
                mock_dependencies["pdf_file"], skip_existing=False
            )

            assert result.book_id == 123
            assert result.skipped is False
            # exists_by_title should not have been called
            mock_book_repo.exists_by_title.assert_not_called()


class TestBatchUploadCLI:
    """Tests for batch_upload.py CLI script."""

    def test_scan_pdf_files_success(self, tmp_path: Path):
        """Scan directory should find PDF files."""
        from batch_upload import scan_pdf_files

        # Create test PDF files
        (tmp_path / "file1.pdf").write_bytes(b"%PDF-1.4")
        (tmp_path / "file2.pdf").write_bytes(b"%PDF-1.4")
        (tmp_path / "file3.txt").write_bytes(b"not a pdf")

        result = scan_pdf_files(tmp_path)

        assert len(result) == 2
        assert all(p.suffix == ".pdf" for p in result)

    def test_scan_pdf_files_empty_directory(self, tmp_path: Path):
        """Scan empty directory should return empty list."""
        from batch_upload import scan_pdf_files

        result = scan_pdf_files(tmp_path)

        assert result == []

    def test_scan_pdf_files_not_found(self, tmp_path: Path):
        """Scan non-existent directory should raise FileNotFoundError."""
        from batch_upload import scan_pdf_files

        with pytest.raises(FileNotFoundError):
            scan_pdf_files(tmp_path / "nonexistent")

    def test_scan_pdf_files_not_directory(self, tmp_path: Path):
        """Scan file instead of directory should raise NotADirectoryError."""
        from batch_upload import scan_pdf_files

        file_path = tmp_path / "file.txt"
        file_path.write_text("test")

        with pytest.raises(NotADirectoryError):
            scan_pdf_files(file_path)

    def test_batch_result_elapsed_time(self):
        """BatchResult elapsed time calculation."""
        from batch_upload import BatchResult

        result = BatchResult()
        result.start_time = 0.0
        result.end_time = 125.5  # 2m 5.5s

        assert result.elapsed_time == 125.5
        assert "2m" in result.elapsed_time_str

    def test_save_failed_list(self, tmp_path: Path):
        """Failed list should be saved to file."""
        from batch_upload import save_failed_list

        failed_list = [
            ("file1.pdf", "Parse error"),
            ("file2.pdf", "Indexing error"),
        ]
        output_path = tmp_path / "failed.txt"

        save_failed_list(failed_list, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "file1.pdf" in content
        assert "Parse error" in content
        assert "file2.pdf" in content

    @pytest.mark.asyncio
    async def test_run_batch_upload_dry_run(self, tmp_path: Path):
        """Dry run should not process files."""
        from batch_upload import run_batch_upload

        # Create test PDF files
        (tmp_path / "file1.pdf").write_bytes(b"%PDF-1.4")
        (tmp_path / "file2.pdf").write_bytes(b"%PDF-1.4")

        result = await run_batch_upload(
            source_dir=tmp_path,
            dry_run=True,
        )

        assert result.total == 2
        assert result.success == 0
        assert result.failed == 0

    @pytest.mark.asyncio
    async def test_run_batch_upload_success(self, tmp_path: Path):
        """Batch upload should process files successfully."""
        from batch_upload import run_batch_upload

        # Create test PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 test content")

        mock_result = BatchIndexingResult(
            book_id=123,
            title="test",
            chunks_count=10,
            file_path="/storage/uuid.pdf",
            status="indexed",
        )

        with patch(
            "batch_upload.index_local_pdf",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await run_batch_upload(
                source_dir=tmp_path,
                skip_existing=True,
                parallel=1,  # Sequential mode
            )

            assert result.total == 1
            assert result.success == 1
            assert result.failed == 0

    @pytest.mark.asyncio
    async def test_run_batch_upload_parallel(self, tmp_path: Path):
        """Batch upload should work in parallel mode."""
        from batch_upload import run_batch_upload

        # Create test PDF files
        for i in range(3):
            (tmp_path / f"test{i}.pdf").write_bytes(b"%PDF-1.4 test")

        mock_result = BatchIndexingResult(
            book_id=123,
            title="test",
            chunks_count=10,
            file_path="/storage/uuid.pdf",
            status="indexed",
        )

        with patch(
            "batch_upload.index_local_pdf",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            result = await run_batch_upload(
                source_dir=tmp_path,
                skip_existing=True,
                parallel=2,  # Parallel mode
            )

            assert result.total == 3
            assert result.success == 3
            assert result.failed == 0

    @pytest.mark.asyncio
    async def test_run_batch_upload_with_failures(self, tmp_path: Path):
        """Batch upload should handle failures gracefully."""
        from batch_upload import run_batch_upload

        # Create test PDF files
        (tmp_path / "good.pdf").write_bytes(b"%PDF-1.4")
        (tmp_path / "bad.pdf").write_bytes(b"%PDF-1.4")

        mock_results = [
            BatchIndexingResult(
                book_id=123,
                title="good",
                chunks_count=10,
                file_path="/storage/uuid.pdf",
            ),
            None,  # Simulate failure for second file
        ]

        async def mock_index(*args, **kwargs):
            return mock_results.pop(0)

        with patch("batch_upload.index_local_pdf", side_effect=mock_index):
            result = await run_batch_upload(
                source_dir=tmp_path,
                parallel=1,  # Sequential mode
            )

            assert result.total == 2
            assert result.success == 1
            assert result.failed == 1

    @pytest.mark.asyncio
    async def test_run_batch_upload_race_condition_handled(self, tmp_path: Path):
        """DuplicateBookError during parallel processing should be treated as skip."""
        from batch_upload import run_batch_upload

        # Create test PDF file
        (tmp_path / "test.pdf").write_bytes(b"%PDF-1.4")

        async def mock_index_raises(*args, **kwargs):
            raise DuplicateBookError("test.pdf")

        with patch("batch_upload.index_local_pdf", side_effect=mock_index_raises):
            result = await run_batch_upload(
                source_dir=tmp_path,
                skip_existing=True,  # Should treat DuplicateBookError as skip
                parallel=1,
            )

            # Should be skipped, not failed
            assert result.total == 1
            assert result.skipped == 1
            assert result.failed == 0
