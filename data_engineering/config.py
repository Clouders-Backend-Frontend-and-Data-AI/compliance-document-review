from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Data-engineering settings. All fields optional so the package imports under SQLite/offline."""

    database_url: str = Field(default="sqlite:///./compliance_app.db", alias="DATABASE_URL")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    embedding_model: str = Field(default="models/text-embedding-004", alias="EMBEDDING_MODEL")
    embedding_dimension: int = Field(default=768, alias="EMBEDDING_DIMENSION")

    chunk_size_tokens: int = Field(default=400, alias="CHUNK_SIZE_TOKENS")
    chunk_overlap_tokens: int = Field(default=60, alias="CHUNK_OVERLAP_TOKENS")

    rule_retrieval_top_k: int = Field(default=5, alias="RULE_RETRIEVAL_TOP_K")
    disclosure_similarity_threshold: float = Field(
        default=0.78, alias="DISCLOSURE_SIMILARITY_THRESHOLD"
    )
    precedent_top_k: int = Field(default=3, alias="PRECEDENT_TOP_K")

    max_file_size_bytes: int = Field(default=10 * 1024 * 1024, alias="MAX_FILE_SIZE_BYTES")
    embedding_batch_size: int = Field(default=20, alias="EMBEDDING_BATCH_SIZE")

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def uses_pgvector(self) -> bool:
        return self.database_url.startswith("postgresql")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
