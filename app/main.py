import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.router import api_router

# Import all models to ensure declarative metadata registration
import app.models

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Database Tables
    Base.metadata.create_all(bind=engine)
    # Ensure upload directory exists
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
- **Vector Search Engine**: Rule lookup, disclosure-by-absence detection, and top-3 precedent matching.
- **AI Assist with Graceful Fallback**: Traceable flags and summaries without blocking reviewers if AI is offline.
- **Revision Threading**: Ordered document version history and resubmissions.
- **Append-Only Audit Trail & In-App Notifications**.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", tags=["Health"])
def root():
    return {
        "service": settings.PROJECT_NAME,
        "status": "online",
        "docs_url": "/docs",
        "api_v1_prefix": settings.API_V1_STR
    }

@app.get(f"{settings.API_V1_STR}/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "ai_status": "ready" if settings.GEMINI_API_KEY else "fallback_mode (no key set)"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
