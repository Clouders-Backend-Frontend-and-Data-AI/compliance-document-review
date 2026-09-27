from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.documents import router as documents_router
from app.api.v1.reviews import router as reviews_router
from app.api.v1.audit import router as audit_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.corpus import router as corpus_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(documents_router)
api_router.include_router(reviews_router)
api_router.include_router(audit_router)
api_router.include_router(notifications_router)
api_router.include_router(corpus_router)
