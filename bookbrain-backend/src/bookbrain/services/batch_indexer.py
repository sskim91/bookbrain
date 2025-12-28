"""Batch indexing service for processing local PDF files."""

import logging
import shutil
import uuid
from pathlib import Path

from pydantic import BaseModel

from bookbrain.core.config import settings
from bookbrain.core.exceptions import (
    DuplicateBookError,
    IndexingError,
    InvalidFileFormatError,
    PDFReadError,
)
from bookbrain.repositories import book_repository
from bookbrain.services.chunker import chunk_text
from bookbrain.services.indexer import IndexingResult, index_book
from bookbrain.services.parser import parse_pdf
from bookbrain.services.storage import (
    delete_parsed_result_from_s3,
    delete_stored_file,
    save_parsed_result_to_s3,
    upload_temp_to_s3,
)

logger = logging.getLogger(__name__)

# PDF Magic Number (file signature)
PDF_MAGIC_NUMBER = b"%PDF-"


class BatchIndexingResult(BaseModel):
    """Result of batch indexing a single PDF file."""

    book_id: int | None = None
    title: str
    chunks_count: int = 0
    file_path: str | None = None
    status: str = "indexed"
    skipped: bool = False
    skip_reason: str | None = None


def validate_pdf_file_path(file_path: Path) -> None:
    """
    Validate that a local file is a valid PDF.

    Performs validation:
    1. File exists check
    2. File extension check
    3. Magic Number (file header) check for security

    Args:
        file_path: Path to the local PDF file

    Raises:
        InvalidFileFormatError: If the file is not a valid PDF
        PDFReadError: If the file cannot be read
    """
    filename = file_path.name

    # Check file exists
    if not file_path.exists():
        raise PDFReadError(str(file_path))

    if not file_path.is_file():
        raise PDFReadError(str(file_path))

    # Check file extension
    if not filename.lower().endswith(".pdf"):
        raise InvalidFileFormatError(filename)

    # Check Magic Number (file header) - most reliable check
    try:
        with open(file_path, "rb") as f:
            header = f.read(len(PDF_MAGIC_NUMBER))
    except OSError as e:
        raise PDFReadError(str(file_path), cause=e)

    if not header.startswith(PDF_MAGIC_NUMBER):
        raise InvalidFileFormatError(filename)


def copy_to_local_storage(source_path: Path) -> str:
    """
    Copy a local file to the permanent storage directory.

    Args:
        source_path: Source file path

    Returns:
        Path to the copied file in storage
    """
    storage_dir = Path(settings.pdf_storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)

    file_id = str(uuid.uuid4())
    dest_path = storage_dir / f"{file_id}.pdf"

    shutil.copy2(source_path, dest_path)
    logger.info(f"Copied file to local storage: {dest_path}")
    return str(dest_path)


async def index_local_pdf(
    file_path: Path,
    title: str | None = None,
    author: str | None = None,
    skip_existing: bool = True,
) -> BatchIndexingResult:
    """
    Index a local PDF file.

    This function orchestrates the full indexing pipeline for local files:
    1. Validate PDF file
    2. Check for duplicates (optional)
    3. Parse PDF (Storm Parse API)
    4. Copy/upload to permanent storage (S3 or local)
    5. Create book record in PostgreSQL
    6. Save parsed result to S3 (optional)
    7. Chunk text
    8. Index (embed + store in Qdrant)

    Args:
        file_path: Path to the local PDF file
        title: Book title (optional, defaults to filename without extension)
        author: Book author (optional)
        skip_existing: If True, skip files with matching titles (default: True)

    Returns:
        BatchIndexingResult with book_id, title, and chunks_count

    Raises:
        InvalidFileFormatError: If the file is not a valid PDF
        PDFReadError: If the file cannot be read
        DuplicateBookError: If skip_existing is False and title exists
        IndexingError: If indexing fails at any step
    """
    stored_path: str | None = None
    book_id: int | None = None
    book_title = title or file_path.stem

    try:
        # 1. Validate PDF file
        validate_pdf_file_path(file_path)

        # 2. Check for duplicates
        if skip_existing:
            exists = await book_repository.exists_by_title(book_title)
            if exists:
                logger.info(f"Skipping duplicate: {book_title}")
                return BatchIndexingResult(
                    title=book_title,
                    status="skipped",
                    skipped=True,
                    skip_reason=f"Book with title '{book_title}' already exists",
                )

        # 3. Parse PDF from local file (no need to copy first)
        parse_result = await parse_pdf(str(file_path))

        # 4. Copy/upload to permanent storage
        if settings.s3_enabled:
            # Upload directly from source path
            stored_path = upload_temp_to_s3(str(file_path))
        else:
            # Copy to local storage directory
            stored_path = copy_to_local_storage(file_path)

        # 5. Create book record
        book_id = await book_repository.create_book(
            title=book_title,
            file_path=stored_path,
            author=author,
        )

        # 6. Save parsed result to S3 (optional, non-blocking on failure)
        if settings.s3_enabled:
            parsed_result_path = save_parsed_result_to_s3(
                book_id, parse_result.raw_response
            )
            if parsed_result_path:
                logger.info(f"Saved parsed result to: {parsed_result_path}")

        # 7. Chunk text
        chunked_doc = chunk_text(parse_result.document)

        # 8. Index (embed + store in Qdrant)
        result: IndexingResult = await index_book(book_id, chunked_doc)

        return BatchIndexingResult(
            book_id=book_id,
            title=book_title,
            chunks_count=result.chunks_stored,
            file_path=stored_path,
            status="indexed",
        )

    except (InvalidFileFormatError, PDFReadError, DuplicateBookError):
        # These are expected errors, re-raise without cleanup
        raise

    except IndexingError as e:
        # Cleanup on indexing failure
        if book_id is not None:
            try:
                await book_repository.delete_book(book_id)
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup book {book_id}: {cleanup_error}")

            # Cleanup parsed result from S3
            if settings.s3_enabled:
                delete_parsed_result_from_s3(book_id)

        if stored_path:
            delete_stored_file(stored_path)

        raise

    except Exception as e:
        logger.exception(f"Unexpected error during batch indexing: {e}")

        # Cleanup on failure
        if book_id is not None:
            try:
                await book_repository.delete_book(book_id)
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup book {book_id}: {cleanup_error}")

            if settings.s3_enabled:
                delete_parsed_result_from_s3(book_id)

        if stored_path:
            delete_stored_file(stored_path)

        raise IndexingError(f"Failed to index {file_path}: {e}", cause=e) from e
