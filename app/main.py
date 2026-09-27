import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.security_headers import SecurityHeadersMiddleware

import app.models  # noqa: F401

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
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

Production-oriented, role-governed compliance review backend for financial advisor materials.

## Guarantees
- Server-side role enforcement (advisor / officer)
- PII masked before LLM / embedding calls
- PDF / DOCX / XLSX uploads (10MB)
- Vector assist with graceful degradation
- Revision threading + append-only audit + in-app notifications
    """,
    version="1.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
)

# Trusted hosts (skip wildcard in production via config validation)
hosts = settings.ALLOWED_HOSTS
if hosts and hosts != ["*"]:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)

app.add_middleware(SecurityHeadersMiddleware)

cors_origins = settings.BACKEND_CORS_ORIGINS
allow_credentials = cors_origins != ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    detail = "Internal server error"
    if not settings.is_production:
        detail = f"Internal server error: {exc}"
    return JSONResponse(status_code=500, content={"detail": detail})


@app.get("/", tags=["Health"])
def root():
    return {
        "service": settings.PROJECT_NAME,
        "status": "online",
        "docs_url": "/docs" if settings.docs_enabled else None,
        "api_v1_prefix": settings.API_V1_STR,
        "environment": settings.ENVIRONMENT,
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

    payload = {
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
    if db_status != "connected":
        return JSONResponse(status_code=503, content=payload)
    return payload


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
