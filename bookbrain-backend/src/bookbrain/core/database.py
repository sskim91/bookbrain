"""PostgreSQL database connection and utilities."""

import warnings
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import psycopg
from psycopg.rows import dict_row

from bookbrain.core.config import settings


async def _create_connection() -> psycopg.AsyncConnection:
    """Internal: Create a new async database connection."""
    return await psycopg.AsyncConnection.connect(
        settings.database_url,
        row_factory=dict_row,
    )


async def get_connection() -> psycopg.AsyncConnection:
    """
    Create a new async database connection.

    Warning:
        Prefer using `get_db()` context manager instead.
        Direct use of this function requires manual connection management
        and may lead to resource leaks if not properly closed.

    Returns:
        A new database connection. Caller is responsible for closing it.
    """
    warnings.warn(
        "get_connection() requires manual close. Prefer get_db() context manager.",
        stacklevel=2,
    )
    return await _create_connection()


@asynccontextmanager
async def get_db() -> AsyncGenerator[psycopg.AsyncConnection]:
    """Context manager for database connections."""
    conn = await _create_connection()
    try:
        yield conn
    finally:
        await conn.close()


async def init_db() -> None:
    """Initialize database schema by running init-db.sql."""
    import importlib.resources as resources

    # Read the init SQL file
    sql_path = resources.files("bookbrain").parent.parent / "scripts" / "init-db.sql"

    async with await _create_connection() as conn:
        with open(sql_path) as f:
            sql = f.read()
        await conn.execute(sql)
        await conn.commit()
