import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import Base, engine

# Import all models to ensure declarative metadata registration
import app.models  # noqa: F401

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.validate_security_or_raise()
    if settings.is_insecure_secret():
        logger.warning(
            "SECRET_KEY is an insecure development default. "
            "Set a strong SECRET_KEY before any real deployment."
        )
    Base.metadata.create_all(bind=engine)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
# Compliance Document Review API

A secure, role-governed compliance review backend for financial advisor client-facing materials.

## Key Features:
- **Strict Role Boundaries**: Server-side 403 enforcement for `advisor` and `officer` roles.
- **Server-Side PII Masker**: Zero client PII leaves the app perimeter in LLM prompts or embeddings.
- **Multi-Format Ingestion**: PDF, DOCX, and XLSX text extraction (10MB upload limit).
- **Vector Search Engine**: Rule lookup, disclosure-by-absence detection, and top-3 precedent matching
  (via `data_engineering` when Postgres/pgvector is enabled).
- **AI Assist with Graceful Fallback**: Traceable flags and summaries without blocking reviewers if AI is offline.
- **Revision Threading**: Ordered document version history and resubmissions.
- **Append-Only Audit Trail & In-App Notifications**.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

cors_origins = settings.BACKEND_CORS_ORIGINS
allow_credentials = True
if cors_origins == ["*"]:
    # Browsers reject credentialed requests with wildcard origins
    allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Health"])
def root():
    return {
        "service": settings.PROJECT_NAME,
        "status": "online",
        "docs_url": "/docs",
        "api_v1_prefix": settings.API_V1_STR,
    }


@app.get(f"{settings.API_V1_STR}/health", tags=["Health"])
def health_check():
    db_status = "disconnected"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        logger.warning("Health DB check failed: %s", exc)
        db_status = "error"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "ai_status": "ready" if settings.GEMINI_API_KEY else "fallback_mode (no key set)",
        "data_engineering": (
            "pgvector"
            if settings.USE_DATA_ENGINEERING
            and (settings.DATABASE_URL or "").lower().startswith("postgresql")
            else "local_fallback"
        ),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
