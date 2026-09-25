from typing import List, Optional, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Compliance Document Review API"
    API_V1_STR: str = "/api/v1"
    # Empty / known-insecure defaults are rejected at startup unless ALLOW_INSECURE_DEFAULTS=true
    SECRET_KEY: str = "CHANGE_ME_SET_SECRET_KEY_IN_ENV"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    ALLOW_INSECURE_DEFAULTS: bool = True
    ENVIRONMENT: str = "development"
    # When true (or ENVIRONMENT=test), allow .txt/.md uploads for automated tests only
    ALLOW_PLAINTEXT_UPLOADS: bool = False

    DATABASE_URL: str = "sqlite:///./compliance_app.db"

    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    GEMINI_API_KEY: Optional[str] = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    AI_TIMEOUT_SECONDS: int = 30

    DISCLOSURE_ABSENCE_THRESHOLD: float = 0.60
    PRECEDENT_TOP_K: int = 3
    RULE_RETRIEVAL_TOP_K: int = 5
    EMBEDDING_DIMENSION: int = 768

    # When true and DATABASE_URL is Postgres, use data_engineering pgvector pipeline
    USE_DATA_ENGINEERING: bool = True

    BACKEND_CORS_ORIGINS: Union[List[str], str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ]
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if v is None or v == "":
            return [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173",
            ]
        if isinstance(v, str):
            if v.strip() == "*":
                return ["*"]
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    def is_insecure_secret(self) -> bool:
        insecure = {
            "",
            "CHANGE_ME_SET_SECRET_KEY_IN_ENV",
            "super-secret-key-for-jwt-change-in-production",
            "secret",
            "changeme",
            "CHANGE-ME-IN-PRODUCTION",
            "replace-with-a-long-random-string",
        }
        return (self.SECRET_KEY or "").strip() in insecure

    def validate_security_or_raise(self) -> None:
        if self.is_insecure_secret():
            if self.ALLOW_INSECURE_DEFAULTS and self.ENVIRONMENT.lower() != "production":
                return
            raise RuntimeError(
                "SECRET_KEY is missing or uses an insecure default. "
                "Set a strong SECRET_KEY in the environment."
            )


settings = Settings()
