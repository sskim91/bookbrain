"""PostgreSQL database connection pool and utilities."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from bookbrain.core.config import settings

# Global connection pool (initialized lazily)
_pool: AsyncConnectionPool | None = None


async def _get_pool() -> AsyncConnectionPool:
    """Get or create the global connection pool."""
    global _pool
    if _pool is None:
        _pool = AsyncConnectionPool(
            conninfo=settings.database_url,
            min_size=1,
            max_size=10,
            kwargs={"row_factory": dict_row},
            open=False,
        )
        await _pool.open()
    return _pool


@asynccontextmanager
async def get_db() -> AsyncGenerator[psycopg.AsyncConnection]:
    """
    Context manager for database connections from the pool.

    Connections are automatically returned to the pool when done.
    This is the recommended way to get database connections.

    Usage:
        async with get_db() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT ...")
    """
    pool = await _get_pool()
    async with pool.connection() as conn:
        yield conn


async def close_pool() -> None:
    """
    Close the connection pool.

    Call this during application shutdown to cleanly release all connections.
    """
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def init_db() -> None:
    """Initialize database schema by running init-db.sql."""
    import importlib.resources as resources

    # Read the init SQL file
    sql_path = resources.files("bookbrain").parent.parent / "scripts" / "init-db.sql"

    async with get_db() as conn:
        with open(sql_path) as f:
            sql = f.read()
        await conn.execute(sql)
        await conn.commit()
