"""Repository for book metadata CRUD operations."""

from datetime import datetime
from typing import TypedDict

import psycopg
from psycopg.rows import dict_row

from bookbrain.core.database import get_db
from bookbrain.core.exceptions import BookCreationError, DuplicateBookError


class Book(TypedDict):
    """Book record type."""

    id: int
    title: str
    author: str | None
    file_path: str
    total_pages: int | None
    embedding_model: str | None
    created_at: datetime


async def create_book(
    title: str,
    file_path: str,
    author: str | None = None,
    total_pages: int | None = None,
    embedding_model: str | None = None,
    conn: psycopg.AsyncConnection | None = None,
) -> int:
    """
    Create a new book record.

    Args:
        title: Book title
        file_path: Path to the PDF file
        author: Book author (optional)
        total_pages: Total number of pages (optional)
        embedding_model: Embedding model version used (optional)
        conn: Optional existing database connection (caller manages transaction)

    Returns:
        The ID of the created book

    Note:
        If conn is provided, the caller is responsible for committing.
        If conn is None, this function commits automatically.
    """
    query = """
        INSERT INTO books (title, author, file_path, total_pages, embedding_model)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """

    async def execute(
        connection: psycopg.AsyncConnection, auto_commit: bool
    ) -> int:
        try:
            async with connection.cursor(row_factory=dict_row) as cur:
                await cur.execute(
                    query, (title, author, file_path, total_pages, embedding_model)
                )
                result = await cur.fetchone()
                if result is None:
                    raise BookCreationError("Failed to create book: no ID returned")
                if auto_commit:
                    await connection.commit()
                return result["id"]
        except psycopg.errors.UniqueViolation as e:
            raise DuplicateBookError(file_path) from e
        except psycopg.Error as e:
            raise BookCreationError(f"Database error: {e}", cause=e) from e

    if conn is not None:
        return await execute(conn, auto_commit=False)

    async with get_db() as connection:
        return await execute(connection, auto_commit=True)


async def get_book(
    book_id: int,
    conn: psycopg.AsyncConnection | None = None,
) -> Book | None:
    """
    Get a book by ID.

    Args:
        book_id: The book ID
        conn: Optional existing database connection

    Returns:
        The book record or None if not found
    """
    query = """
        SELECT id, title, author, file_path, total_pages, embedding_model, created_at
        FROM books
        WHERE id = %s
    """

    async def execute(connection: psycopg.AsyncConnection) -> Book | None:
        async with connection.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, (book_id,))
            result = await cur.fetchone()
            return dict(result) if result else None

    if conn is not None:
        return await execute(conn)

    async with get_db() as connection:
        return await execute(connection)


async def get_books(
    limit: int = 100,
    offset: int = 0,
    conn: psycopg.AsyncConnection | None = None,
) -> list[Book]:
    """
    Get all books with pagination.

    Args:
        limit: Maximum number of books to return
        offset: Number of books to skip
        conn: Optional existing database connection

    Returns:
        List of book records
    """
    query = """
        SELECT id, title, author, file_path, total_pages, embedding_model, created_at
        FROM books
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
    """

    async def execute(connection: psycopg.AsyncConnection) -> list[Book]:
        async with connection.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, (limit, offset))
            results = await cur.fetchall()
            return [dict(row) for row in results]

    if conn is not None:
        return await execute(conn)

    async with get_db() as connection:
        return await execute(connection)


async def delete_book(
    book_id: int,
    conn: psycopg.AsyncConnection | None = None,
) -> bool:
    """
    Delete a book by ID.

    Args:
        book_id: The book ID to delete
        conn: Optional existing database connection (caller manages transaction)

    Returns:
        True if the book was deleted, False if not found

    Note:
        If conn is provided, the caller is responsible for committing.
        If conn is None, this function commits automatically.
    """
    query = """
        DELETE FROM books
        WHERE id = %s
        RETURNING id
    """

    async def execute(
        connection: psycopg.AsyncConnection, auto_commit: bool
    ) -> bool:
        async with connection.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, (book_id,))
            result = await cur.fetchone()
            if auto_commit:
                await connection.commit()
            return result is not None

    if conn is not None:
        return await execute(conn, auto_commit=False)

    async with get_db() as connection:
        return await execute(connection, auto_commit=True)


async def update_book_embedding_model(
    book_id: int,
    embedding_model: str,
    total_pages: int | None = None,
    conn: psycopg.AsyncConnection | None = None,
) -> bool:
    """
    Update the embedding model version (and optionally total_pages) for a book.

    Args:
        book_id: The book ID to update
        embedding_model: The embedding model version used
        total_pages: Total number of pages (optional)
        conn: Optional existing database connection (caller manages transaction)

    Returns:
        True if the book was updated, False if not found

    Note:
        If conn is provided, the caller is responsible for committing.
        If conn is None, this function commits automatically.
    """
    if total_pages is not None:
        query = """
            UPDATE books
            SET embedding_model = %s, total_pages = %s
            WHERE id = %s
            RETURNING id
        """
        params = (embedding_model, total_pages, book_id)
    else:
        query = """
            UPDATE books
            SET embedding_model = %s
            WHERE id = %s
            RETURNING id
        """
        params = (embedding_model, book_id)

    async def execute(
        connection: psycopg.AsyncConnection, auto_commit: bool
    ) -> bool:
        async with connection.cursor(row_factory=dict_row) as cur:
            await cur.execute(query, params)
            result = await cur.fetchone()
            if auto_commit:
                await connection.commit()
            return result is not None

    if conn is not None:
        return await execute(conn, auto_commit=False)

    async with get_db() as connection:
        return await execute(connection, auto_commit=True)
