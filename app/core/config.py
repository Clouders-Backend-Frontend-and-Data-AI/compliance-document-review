from typing import List, Optional, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Compliance Document Review API"
    API_V1_STR: str = "/api/v1"

    SECRET_KEY: str = "CHANGE_ME_SET_SECRET_KEY_IN_ENV"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # production-friendly default
    ALLOW_INSECURE_DEFAULTS: bool = False
    ENVIRONMENT: str = "development"

    # Demo/intern: allow open officer signup. Production must set false.
    ALLOW_OFFICER_SIGNUP: bool = False
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
    USE_DATA_ENGINEERING: bool = True

    BACKEND_CORS_ORIGINS: Union[List[str], str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ]
    )
    ALLOWED_HOSTS: Union[List[str], str] = Field(
        default_factory=lambda: ["localhost", "127.0.0.1", "testserver","compliance-document-review.onrender.com"]
    )

    # Rate limits (per IP, sliding window approx)
    RATE_LIMIT_AUTH_PER_MINUTE: int = 20
    RATE_LIMIT_UPLOAD_PER_MINUTE: int = 30
    ENABLE_RATE_LIMITING: bool = True

    # API docs — disabled automatically when ENVIRONMENT=production
    ENABLE_API_DOCS: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("BACKEND_CORS_ORIGINS", "ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_list(cls, v):
        if v is None or v == "":
            return v
        if isinstance(v, str):
            if v.strip() == "*":
                return ["*"]
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def docs_enabled(self) -> bool:
        if self.is_production:
            return False
        return self.ENABLE_API_DOCS

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
        key = (self.SECRET_KEY or "").strip()
        return key in insecure or len(key) < 32

    def validate_security_or_raise(self) -> None:
        if self.is_production and self.BACKEND_CORS_ORIGINS == ["*"]:
            raise RuntimeError("BACKEND_CORS_ORIGINS=* is not allowed in production.")
        if self.is_insecure_secret():
            allow_dev = (
                self.ALLOW_INSECURE_DEFAULTS
                and self.ENVIRONMENT.lower() in {"development", "test"}
            )
            if not allow_dev:
                raise RuntimeError(
                    "SECRET_KEY is missing, too short (<32), or uses an insecure default. "
                    "Set a strong SECRET_KEY in the environment."
                )


settings = Settings()
