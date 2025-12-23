"""Pytest configuration and fixtures."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from bookbrain.core.config import Settings
from bookbrain.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_db_cursor():
    """Mock PostgreSQL async cursor for repository tests."""
    mock_cursor = AsyncMock()
    mock_cursor.execute = AsyncMock()
    mock_cursor.fetchone = AsyncMock()
    mock_cursor.fetchall = AsyncMock()
    return mock_cursor


@pytest.fixture
def mock_db_connection(mock_db_cursor):
    """
    Mock PostgreSQL async connection for repository tests.

    Properly mocks cursor() to return an async context manager.
    """
    mock_conn = AsyncMock()

    # Create async context manager for cursor
    cursor_context = AsyncMock()
    cursor_context.__aenter__ = AsyncMock(return_value=mock_db_cursor)
    cursor_context.__aexit__ = AsyncMock(return_value=None)

    # cursor() should return the context manager directly (not a coroutine)
    mock_conn.cursor = MagicMock(return_value=cursor_context)
    mock_conn.commit = AsyncMock()
    mock_conn.close = AsyncMock()

    return mock_conn


@pytest.fixture
def mock_qdrant_client():
    """
    Mock Qdrant client for repository tests.

    Note: Using MagicMock because qdrant-client uses synchronous methods.
    For async client (AsyncQdrantClient), use AsyncMock instead.
    """
    mock_client = MagicMock()
    mock_client.upsert = MagicMock()
    mock_client.delete = MagicMock()
    mock_client.scroll = MagicMock(return_value=([], None))
    mock_client.get_collections = MagicMock()
    mock_client.create_collection = MagicMock()
    mock_client.delete_collection = MagicMock()
    return mock_client


@pytest.fixture
def mock_settings():
    """
    Mock settings for parser tests.

    Returns test settings and patches the global settings object.
    """
    test_settings = Settings(
        storm_parse_api_key="test-api-key",
        storm_parse_api_base_url="https://test-api.example.com/v2",
        storm_parse_timeout=5,
        storm_parse_poll_interval=0.1,
        storm_parse_max_poll_attempts=10,
    )

    with patch("bookbrain.services.parser.settings", test_settings):
        yield test_settings
