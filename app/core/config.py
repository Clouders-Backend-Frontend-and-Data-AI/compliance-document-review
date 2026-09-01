import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Compliance Document Review API"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "super-secret-key-for-jwt-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    DATABASE_URL: str = "sqlite:///./compliance_app.db"

    # Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    # AI Configuration (Free tier Gemini recommended)
    GEMINI_API_KEY: Optional[str] = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    AI_TIMEOUT_SECONDS: int = 30

    # Vector Retrieval
    DISCLOSURE_ABSENCE_THRESHOLD: float = 0.60
    PRECEDENT_TOP_K: int = 3
    RULE_RETRIEVAL_TOP_K: int = 5

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
