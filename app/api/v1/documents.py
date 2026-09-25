import os
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, require_advisor
from app.models.user import User
from app.models.base import DocumentType, DocumentStatus
from app.schemas.document import DocumentDetailOut, DocumentListItemOut, DocumentThreadOut, DocumentCreateResponse
from app.services.document_service import DocumentService
from app.services.audit_service import AuditService
from app.models.base import AuditAction

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=DocumentCreateResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    title: str = Form(..., description="Title of the client-facing document"),
    document_type: DocumentType = Form(DocumentType.OTHER, description="Category of document"),
    file: UploadFile = File(..., description="Document file (PDF, DOCX, XLSX, max 10MB)"),
    current_user: User = Depends(require_advisor),
    db: Session = Depends(get_db)
):
    """
    Upload a new compliance document (Advisor Only).
    Initializes document lifecycle in 'pending_review' status.
    Officers attempting to upload receive 403 Forbidden.
    """
    doc = DocumentService.create_document(
        db=db,
        advisor=current_user,
        title=title,
        document_type=document_type,
        file=file
    )
    return {
        "document": doc,
        "message": "Document successfully uploaded and queued for review"
    }

@router.get("", response_model=List[DocumentListItemOut])
def list_documents(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List documents:
    - Advisors receive their own submitted documents.
    - Compliance Officers receive the unified queue across all advisors (filterable by status: pending_review, approved, rejected, needs_revision, all).
    """
    docs = DocumentService.get_documents_for_user(db=db, user=current_user, status_filter=status)
    return [DocumentService.attach_latest_decision(d) for d in docs]

@router.get("/{document_id}", response_model=DocumentDetailOut)
def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve full document details, extracted text, decisions, and cached AI analysis.
    Advisors can only view documents they submitted. Officers can view any document.
    Access is recorded in the audit trail.
    """
    doc = DocumentService.get_document_by_id(db=db, document_id=document_id, user=current_user, log_view=True)
    return DocumentService.attach_latest_decision(doc)

@router.get("/{document_id}/thread", response_model=DocumentThreadOut)
def get_document_thread(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve the entire revision history and thread for a document.
    Enables viewing all versions from original upload to final approval.
    """
    thread_id, thread_docs = DocumentService.get_document_thread(
        db=db,
        document_id=document_id,
        user=current_user
    )
    current_v = max((d.version_number for d in thread_docs), default=1)
    return {
        "thread_id": thread_id,
        "total_versions": len(thread_docs),
        "current_version": current_v,
        "documents": thread_docs
    }

@router.post("/{document_id}/revise", response_model=DocumentCreateResponse, status_code=status.HTTP_201_CREATED)
def submit_revision(
    document_id: str,
    title: str = Form(..., description="Title of the revised document"),
    document_type: DocumentType = Form(DocumentType.OTHER, description="Category of document"),
    file: UploadFile = File(..., description="Revised file (PDF, DOCX, XLSX, max 10MB)"),
    current_user: User = Depends(require_advisor),
    db: Session = Depends(get_db)
):
    """
    Submit a revised version of a document in 'needs_revision' status (Advisor Only).
    Maintains thread linkage and increments version number.
    """
    revised_doc = DocumentService.create_revision(
        db=db,
        advisor=current_user,
        parent_document_id=document_id,
        title=title,
        document_type=document_type,
        file=file
    )
    return {
        "document": revised_doc,
        "message": f"Revision (v{revised_doc.version_number}) successfully submitted and queued for review"
    }

@router.get("/{document_id}/download")
def download_document_file(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download the original uploaded binary file"""
    doc = DocumentService.get_document_by_id(db=db, document_id=document_id, user=current_user, log_view=False)
    if not os.path.exists(doc.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on storage server."
        )

    AuditService.log_event(
        db=db,
        document_id=doc.id,
        action=AuditAction.DOWNLOADED,
        actor=current_user,
        details={"file_name": doc.file_name}
    )

    return FileResponse(
        path=doc.file_path,
        filename=doc.file_name,
        media_type=doc.mime_type
    )
