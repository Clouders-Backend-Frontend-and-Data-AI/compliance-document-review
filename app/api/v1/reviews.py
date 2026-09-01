import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_officer
from app.models.user import User
from app.models.document import Document
from app.models.pii_mapping import PIIMapping
from app.models.base import UserRole
from app.schemas.review import ReviewDecisionCreate, ReviewDecisionOut
from app.schemas.ai_analysis import AIAnalysisOut, OutboundPayloadOut
from app.services.document_service import DocumentService
from app.services.ai_assist import AIAssistService

router = APIRouter(prefix="/documents", tags=["Reviews & AI Assist"])

@router.post("/{document_id}/review", response_model=ReviewDecisionOut, status_code=status.HTTP_201_CREATED)
def submit_review_decision(
    document_id: str,
    decision_in: ReviewDecisionCreate,
    current_user: User = Depends(require_officer),
    db: Session = Depends(get_db)
):
    """
    Record a compliance decision and comment for a document (Compliance Officer Only).
    Allowed decisions: 'approved', 'rejected', 'needs_revision'.
    Advisors hitting this endpoint receive 403 Forbidden.
    """
    _, review_record = DocumentService.record_decision(
        db=db,
        officer=current_user,
        document_id=document_id,
        decision_status=decision_in.status,
        comment=decision_in.comment
    )
    return review_record

@router.get("/{document_id}/assist", response_model=AIAnalysisOut)
def get_ai_assist(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve cached AI assist summary, compliance flags, and top 3 precedent matches.
    If not yet generated, triggers generation.
    Returns gracefully even if third-party LLM API is unavailable.
    """
    doc = DocumentService.get_document_by_id(db=db, document_id=document_id, user=current_user, log_view=False)
    analysis_data = AIAssistService.generate_or_get_analysis(db=db, document=doc, force_regenerate=False)
    return analysis_data

@router.post("/{document_id}/assist/retry", response_model=AIAnalysisOut)
def retry_ai_assist(
    document_id: str,
    current_user: User = Depends(require_officer),
    db: Session = Depends(get_db)
):
    """
    Force re-run AI compliance analysis (Compliance Officer Only).
    Useful when retrying after network errors or adjusting retrieval parameters.
    """
    doc = DocumentService.get_document_by_id(db=db, document_id=document_id, user=current_user, log_view=False)
    analysis_data = AIAssistService.generate_or_get_analysis(db=db, document=doc, force_regenerate=True)
    return analysis_data

@router.get("/{document_id}/outbound-payload", response_model=OutboundPayloadOut)
def inspect_outbound_payload(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Inspect the exact masked text payload sent to external AI and embedding endpoints.
    Provides verifiable proof that client PII (names, emails, phones, SSNs, accounts)
    never escapes the application perimeter.
    """
    doc = DocumentService.get_document_by_id(db=db, document_id=document_id, user=current_user, log_view=False)
    analysis_data = AIAssistService.generate_or_get_analysis(db=db, document=doc, force_regenerate=False)
    
    # Fetch cached payload snapshot or generate it
    analysis_obj = doc.ai_analysis
    masked_payload = analysis_obj.outbound_payload_masked if analysis_obj and analysis_obj.outbound_payload_masked else "Payload not yet generated"
    
    pii_count = db.query(PIIMapping).filter(PIIMapping.document_id == doc.id).count()

    return {
        "document_id": doc.id,
        "masked_payload": masked_payload,
        "pii_entities_masked_count": pii_count,
        "note": "This shows the exact server-side masked payload dispatched to external LLM / embedding endpoints. Zero original PII leaves the app perimeter."
    }
