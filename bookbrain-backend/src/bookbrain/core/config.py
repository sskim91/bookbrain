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

    # OpenAI (for later stories)
    openai_api_key: str = ""

    # Storm Parse (for later stories)
    storm_parse_api_key: str = ""


settings = Settings()
