import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.audit import AuditEventOut
from app.services.audit_service import AuditService
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Audit Trail"])

@router.get("/{document_id}/audit", response_model=List[AuditEventOut])
def get_document_audit_trail(
    document_id: str,
    thread: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve the immutable append-only audit trail for a document.
    Pass ?thread=true to retrieve all audit events across every revision in the thread.
    """
    doc = DocumentService.get_document_by_id(db=db, document_id=document_id, user=current_user, log_view=False)
    
    if thread:
        events = AuditService.get_thread_audit_trail(db=db, thread_id=doc.thread_id)
    else:
        events = AuditService.get_document_audit_trail(db=db, document_id=document_id)

    results = []
    for e in events:
        details_dict = None
        if e.details_json:
            try:
                details_dict = json.loads(e.details_json)
            except Exception:
                details_dict = {"raw": e.details_json}
        results.append({
            "id": e.id,
            "document_id": e.document_id,
            "actor_id": e.actor_id,
            "actor_name": e.actor_name,
            "actor_role": e.actor_role,
            "action": e.action,
            "details": details_dict,
            "created_at": e.created_at
        })

    return results
