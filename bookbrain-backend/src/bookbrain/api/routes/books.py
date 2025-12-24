"""Books API endpoints."""

import logging
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from bookbrain.core.config import settings
from bookbrain.core.exceptions import (
    DuplicateBookError,
    IndexingError,
    InvalidFileFormatError,
)
from bookbrain.models.schemas import (
    BookListResponse,
    BookResponse,
    DeleteResponse,
    IndexingResponse,
)
from bookbrain.repositories import book_repository
from bookbrain.repositories.vector_repository import delete_chunks_by_book_id
from bookbrain.services.chunker import chunk_text
from bookbrain.services.indexer import index_book
from bookbrain.services.parser import parse_pdf

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/books", tags=["books"])


async def save_uploaded_file(file: UploadFile) -> str:
    """
    Save uploaded file to disk.

    Args:
        file: The uploaded file

    Returns:
        The path to the saved file
    """
    storage_dir = Path(settings.pdf_storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)

    file_id = str(uuid.uuid4())
    file_path = storage_dir / f"{file_id}.pdf"

    content = await file.read()
    file_path.write_bytes(content)

    return str(file_path)


def validate_pdf_file(file: UploadFile) -> None:
    """
    Validate that the uploaded file is a PDF.

    Args:
        file: The uploaded file

    Raises:
        InvalidFileFormatError: If the file is not a PDF
    """
    filename = file.filename or ""

    # Check file extension
    if not filename.lower().endswith(".pdf"):
        raise InvalidFileFormatError(filename)

    # Check content type
    content_type = file.content_type or ""
    if content_type and content_type != "application/pdf":
        # Allow empty content type (some clients don't send it)
        if content_type != "application/octet-stream":
            raise InvalidFileFormatError(filename)


@router.post("", response_model=IndexingResponse)
async def upload_book(
    file: UploadFile = File(...),
    title: str | None = Form(None),
    author: str | None = Form(None),
) -> IndexingResponse:
    """
    Upload a PDF and index it.

    The full indexing pipeline is executed:
    1. Save PDF file
    2. Create book record in PostgreSQL
    3. Parse PDF (Storm Parse API)
    4. Chunk text (tiktoken)
    5. Generate embeddings and store in Qdrant

    Args:
        file: PDF file to upload
        title: Book title (optional, defaults to filename)
        author: Book author (optional)

    Returns:
        IndexingResponse with book_id and chunks_count

    Raises:
        HTTPException: 400 for invalid file format, 500 for indexing errors
    """
    file_path: str | None = None
    book_id: int | None = None

    try:
        # 1. Validate file format
        validate_pdf_file(file)

        # 2. Save file to disk
        file_path = await save_uploaded_file(file)

        # 3. Create book record
        book_title = title or (file.filename or "Untitled").replace(".pdf", "")
        book_id = await book_repository.create_book(
            title=book_title,
            file_path=file_path,
            author=author,
        )

        # 4. Parse PDF
        parsed_doc = await parse_pdf(file_path)

        # 5. Chunk text
        chunked_doc = chunk_text(parsed_doc)

        # 6. Index (embed + store in Qdrant)
        result = await index_book(book_id, chunked_doc)

        return IndexingResponse(
            status="indexed",
            book_id=book_id,
            chunks_count=result.chunks_stored,
        )

    except InvalidFileFormatError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_FILE_FORMAT",
                    "message": str(e),
                    "details": {"filename": e.filename},
                }
            },
        ) from e

    except DuplicateBookError as e:
        raise HTTPException(
            status_code=409,
            detail={
                "error": {
                    "code": "DUPLICATE_BOOK",
                    "message": str(e),
                    "details": {"file_path": e.file_path},
                }
            },
        ) from e

    except IndexingError as e:
        # Cleanup on failure
        if book_id is not None:
            try:
                await book_repository.delete_book(book_id)
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup book {book_id}: {cleanup_error}")

        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup file {file_path}: {cleanup_error}")

        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INDEXING_FAILED",
                    "message": str(e),
                    "details": {},
                }
            },
        ) from e

    except Exception as e:
        logger.exception(f"Unexpected error during book upload: {e}")

        # Cleanup on failure
        if book_id is not None:
            try:
                await book_repository.delete_book(book_id)
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup book {book_id}: {cleanup_error}")

        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup file {file_path}: {cleanup_error}")

        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {},
                }
            },
        ) from e


@router.get("", response_model=BookListResponse)
async def get_books(
    limit: int = 100,
    offset: int = 0,
) -> BookListResponse:
    """
    Get list of indexed books.

    Args:
        limit: Maximum number of books to return (default: 100)
        offset: Number of books to skip (default: 0)

    Returns:
        BookListResponse with list of books and total count
    """
    books = await book_repository.get_books(limit=limit, offset=offset)

    return BookListResponse(
        books=[BookResponse(**book) for book in books],
        total=len(books),
    )


@router.delete("/{book_id}", response_model=DeleteResponse)
async def delete_book(book_id: int) -> DeleteResponse:
    """
    Delete a book and its associated data.

    This deletes:
    1. Book record from PostgreSQL
    2. Chunk vectors from Qdrant
    3. PDF file from disk

    Args:
        book_id: ID of the book to delete

    Returns:
        DeleteResponse with deleted=True if successful

    Raises:
        HTTPException: 404 if book not found
    """
    # Get book to find file path
    book = await book_repository.get_book(book_id)

    if book is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "BOOK_NOT_FOUND",
                    "message": f"Book not found: {book_id}",
                    "details": {"book_id": book_id},
                }
            },
        )

    # Delete from Qdrant first
    try:
        delete_chunks_by_book_id(book_id)
    except Exception as e:
        logger.error(f"Failed to delete chunks for book {book_id}: {e}")
        # Continue with deletion even if Qdrant fails

    # Delete book record from PostgreSQL
    deleted = await book_repository.delete_book(book_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "BOOK_NOT_FOUND",
                    "message": f"Book not found: {book_id}",
                    "details": {"book_id": book_id},
                }
            },
        )

    # Delete PDF file
    file_path = book.get("file_path")
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            # Don't fail the request, file cleanup is best-effort

    return DeleteResponse(deleted=True)
