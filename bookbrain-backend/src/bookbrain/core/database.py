"""PostgreSQL database connection and utilities."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import psycopg
from psycopg.rows import dict_row

from bookbrain.core.config import settings


async def get_connection() -> psycopg.AsyncConnection:
    """Create a new async database connection."""
    return await psycopg.AsyncConnection.connect(
        settings.database_url,
        row_factory=dict_row,
    )


@asynccontextmanager
async def get_db() -> AsyncGenerator[psycopg.AsyncConnection]:
    """Context manager for database connections."""
    conn = await get_connection()
    try:
        yield conn
    finally:
        await conn.close()


async def init_db() -> None:
    """Initialize database schema by running init-db.sql."""
    import importlib.resources as resources

    # Read the init SQL file
    sql_path = resources.files("bookbrain").parent.parent / "scripts" / "init-db.sql"

    async with await get_connection() as conn:
        with open(sql_path) as f:
            sql = f.read()
        await conn.execute(sql)
        await conn.commit()
