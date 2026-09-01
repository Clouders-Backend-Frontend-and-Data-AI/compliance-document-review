import os
import uuid
import shutil
from typing import List, Optional, Tuple
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.config import settings
from app.models.document import Document
from app.models.user import User
from app.models.review import ReviewDecision
from app.models.base import DocumentStatus, DocumentType, AuditAction, UserRole
from app.services.extractor import DocumentExtractor
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.services.vector_engine import VectorEngine
from app.services.pii_masker import PIIMasker
from app.services.ai_assist import AIAssistService

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".txt", ".md"}

class DocumentService:
    """Document lifecycle management, revision threading, and decision workflows"""

    @staticmethod
    def _save_file(file: UploadFile) -> Tuple[str, str, int, str]:
        """Validates and saves uploaded file to local storage"""
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file extension '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
        dest_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

        file.file.seek(0, 2)
        size_bytes = file.file.tell()
        file.file.seek(0)

        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if size_bytes > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File exceeds maximum upload size of {settings.MAX_UPLOAD_SIZE_MB}MB ({size_bytes} bytes)."
            )

        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        mime_type = file.content_type or "application/octet-stream"
        return dest_path, file.filename or "unknown", size_bytes, mime_type

    @classmethod
    def create_document(
        cls,
        db: Session,
        advisor: User,
        title: str,
        document_type: DocumentType,
        file: UploadFile
    ) -> Document:
        """Initial submission by an Advisor"""
        file_path, file_name, file_size, mime_type = cls._save_file(file)

        # Extract text
        try:
            extracted_text = DocumentExtractor.extract_text_from_file(file_path, mime_type)
        except Exception as e:
            extracted_text = f"Text extraction warning: {str(e)}"

        thread_uuid = str(uuid.uuid4())
        doc = Document(
            advisor_id=advisor.id,
            title=title,
            document_type=document_type,
            status=DocumentStatus.PENDING_REVIEW,
            file_name=file_name,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            extracted_text=extracted_text,
            thread_id=thread_uuid,
            parent_document_id=None,
            version_number=1
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Log audit event
        AuditService.log_event(
            db=db,
            document_id=doc.id,
            action=AuditAction.SUBMITTED,
            actor=advisor,
            details={"title": title, "file_name": file_name, "version": 1}
        )

        # Automatically trigger AI Assist analysis in the background
        try:
            AIAssistService.generate_or_get_analysis(db, doc)
            AuditService.log_event(
                db=db,
                document_id=doc.id,
                action=AuditAction.ANALYSIS_GENERATED,
                actor=None,
                details={"model": "gemini-1.5-flash"}
            )
        except Exception as e:
            # Never let AI failure crash document creation
            pass

        return doc

    @classmethod
    def create_revision(
        cls,
        db: Session,
        advisor: User,
        parent_document_id: str,
        title: str,
        document_type: DocumentType,
        file: UploadFile
    ) -> Document:
        """Submitting a revised version of a document that was flagged as Needs Revision"""
        parent = db.query(Document).filter(Document.id == parent_document_id).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent document not found."
            )

        if parent.advisor_id != advisor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only revise documents you originally submitted."
            )

        if parent.status != DocumentStatus.NEEDS_REVISION:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Revisions can only be submitted for documents in '{DocumentStatus.NEEDS_REVISION.value}' status. Current status: '{parent.status.value}'."
            )

        file_path, file_name, file_size, mime_type = cls._save_file(file)

        try:
            extracted_text = DocumentExtractor.extract_text_from_file(file_path, mime_type)
        except Exception as e:
            extracted_text = f"Text extraction warning: {str(e)}"

        revised_doc = Document(
            advisor_id=advisor.id,
            title=title,
            document_type=document_type,
            status=DocumentStatus.PENDING_REVIEW,
            file_name=file_name,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            extracted_text=extracted_text,
            thread_id=parent.thread_id,
            parent_document_id=parent.id,
            version_number=parent.version_number + 1
        )
        db.add(revised_doc)
        db.commit()
        db.refresh(revised_doc)

        # Log audit resubmission event
        AuditService.log_event(
            db=db,
            document_id=revised_doc.id,
            action=AuditAction.RESUBMITTED,
            actor=advisor,
            details={
                "parent_document_id": parent.id,
                "version": revised_doc.version_number,
                "file_name": file_name
            }
        )

        # Trigger AI analysis for the revision
        try:
            AIAssistService.generate_or_get_analysis(db, revised_doc)
            AuditService.log_event(
                db=db,
                document_id=revised_doc.id,
                action=AuditAction.ANALYSIS_GENERATED,
                actor=None,
                details={"model": "gemini-1.5-flash"}
            )
        except Exception:
            pass

        return revised_doc

    @classmethod
    def record_decision(
        cls,
        db: Session,
        officer: User,
        document_id: str,
        decision_status: DocumentStatus,
        comment: str
    ) -> Tuple[Document, ReviewDecision]:
        """Compliance Officer records a final human decision and commentary"""
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found."
            )

        if decision_status == DocumentStatus.PENDING_REVIEW:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Decision status cannot be 'pending_review'. Choose 'approved', 'rejected', or 'needs_revision'."
            )

        # Update Document status
        doc.status = decision_status

        # Create ReviewDecision record
        review_record = ReviewDecision(
            document_id=doc.id,
            officer_id=officer.id,
            status=decision_status,
            comment=comment
        )
        db.add(review_record)
        db.commit()
        db.refresh(doc)
        db.refresh(review_record)

        # Log audit decision event
        AuditService.log_event(
            db=db,
            document_id=doc.id,
            action=AuditAction.DECIDED,
            actor=officer,
            details={
                "decision": decision_status.value,
                "comment": comment
            }
        )

        # Create in-app notification for the advisor
        status_label = decision_status.value.replace('_', ' ').title()
        NotificationService.create_notification(
            db=db,
            user_id=doc.advisor_id,
            document_id=doc.id,
            title=f"Document {status_label}: {doc.title}",
            message=f"Compliance Officer {officer.full_name} marked version {doc.version_number} as '{status_label}'. Comment: \"{comment}\""
        )

        # Index as precedent in vector corpus
        try:
            raw_text = doc.extracted_text or ""
            masked_text, _ = PIIMasker.mask_text(raw_text, document_id=doc.id, db=db)
            VectorEngine.index_reviewed_document_as_precedent(
                db=db,
                document_id=doc.id,
                title=doc.title,
                document_type=doc.document_type,
                masked_text=masked_text,
                decision=decision_status,
                officer_comment=comment
            )
        except Exception:
            pass

        return doc, review_record

    @classmethod
    def get_documents_for_user(
        cls,
        db: Session,
        user: User,
        status_filter: Optional[str] = None
    ) -> List[Document]:
        """
        Retrieves document list:
        - Advisors see their own submissions
        - Officers see queue across all advisors, with optional status filter
        """
        query = db.query(Document)

        if user.role == UserRole.ADVISOR:
            query = query.filter(Document.advisor_id == user.id)

        if status_filter and status_filter.lower() != "all":
            try:
                s_enum = DocumentStatus(status_filter.lower())
                query = query.filter(Document.status == s_enum)
            except ValueError:
                pass

        return query.order_by(desc(Document.uploaded_at)).all()

    @classmethod
    def get_document_by_id(
        cls,
        db: Session,
        document_id: str,
        user: User,
        log_view: bool = True
    ) -> Document:
        """Retrieves a single document, verifying ownership for advisors and logging view audit event"""
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found."
            )

        if user.role == UserRole.ADVISOR and doc.advisor_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this document."
            )

        if log_view:
            AuditService.log_event(
                db=db,
                document_id=doc.id,
                action=AuditAction.VIEWED,
                actor=user,
                details={"viewer_role": user.role.value}
            )

        return doc

    @classmethod
    def get_document_thread(
        cls,
        db: Session,
        document_id: str,
        user: User
    ) -> Tuple[str, List[Document]]:
        """Retrieves full ordered revision chain for a document thread"""
        current_doc = cls.get_document_by_id(db, document_id, user, log_view=False)
        thread_docs = db.query(Document).filter(
            Document.thread_id == current_doc.thread_id
        ).order_by(Document.version_number.asc()).all()

        return current_doc.thread_id, thread_docs
