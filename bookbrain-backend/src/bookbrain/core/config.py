"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql://bookbrain:bookbrain@localhost:5432/bookbrain"

    # Vector Database
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "chunks"
    vector_size: int = 1536  # OpenAI text-embedding-3

    # OpenAI
    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    embedding_batch_size: int = 100
    embedding_max_retries: int = 3
    embedding_retry_base_delay: float = 1.0

    # Storm Parse API
    storm_parse_api_key: str = ""
    storm_parse_api_base_url: str = "https://storm-apis.sionic.im/parse-router/api/v2"
    storm_parse_timeout: int = 30
    storm_parse_poll_interval: float = 2.0
    storm_parse_max_poll_attempts: int = 150

    # File storage
    data_dir: str = "data"
    pdf_storage_dir: str = "data/pdfs"
    max_upload_size: int = 100 * 1024 * 1024  # 100MB


settings = Settings()
