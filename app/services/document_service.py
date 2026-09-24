import logging
import os
import re
import shutil
import uuid
from typing import List, Optional, Tuple

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.base import AuditAction, DocumentStatus, DocumentType, UserRole
from app.models.document import Document
from app.models.review import ReviewDecision
from app.models.user import User
from app.services.ai_assist import AIAssistService
from app.services.audit_service import AuditService
from app.services.extractor import DocumentExtractor
from app.services.notification_service import NotificationService
from app.services.pii_masker import PIIMasker
from app.services.vector_engine import VectorEngine

logger = logging.getLogger(__name__)

BRIEF_EXTENSIONS = {".pdf", ".docx", ".xlsx"}
TEST_EXTENSIONS = {".txt", ".md"}


def _allowed_extensions() -> set:
    allowed = set(BRIEF_EXTENSIONS)
    if settings.ALLOW_PLAINTEXT_UPLOADS or settings.ENVIRONMENT.lower() == "test":
        allowed |= TEST_EXTENSIONS
    return allowed


class DocumentService:
    """Document lifecycle management, revision threading, and decision workflows"""

    @staticmethod
    def _safe_filename(raw_name: Optional[str]) -> str:
        name = os.path.basename(raw_name or "upload.bin")
        name = name.replace("\x00", "")
        name = re.sub(r"[^\w.\- ()]", "_", name).strip(" .")
        if not name or name in {".", ".."}:
            name = "upload.bin"
        # Prevent extension spoofing via trailing dots/spaces
        return name[:180]

    @classmethod
    def _save_file(cls, file: UploadFile) -> Tuple[str, str, int, str]:
        original_name = cls._safe_filename(file.filename)
        ext = os.path.splitext(original_name)[1].lower()
        allowed = _allowed_extensions()
        if ext not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Unsupported file extension '{ext}'. "
                    f"Allowed: {', '.join(sorted(BRIEF_EXTENSIONS))}"
                ),
            )

        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        unique_filename = f"{uuid.uuid4().hex}_{original_name}"
        dest_path = os.path.abspath(os.path.join(settings.UPLOAD_DIR, unique_filename))
        upload_root = os.path.abspath(settings.UPLOAD_DIR)
        if not dest_path.startswith(upload_root + os.sep) and dest_path != upload_root:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file path.",
            )

        file.file.seek(0, 2)
        size_bytes = file.file.tell()
        file.file.seek(0)

        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if size_bytes > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"File exceeds maximum upload size of {settings.MAX_UPLOAD_SIZE_MB}MB "
                    f"({size_bytes} bytes)."
                ),
            )

        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        mime_type = file.content_type or "application/octet-stream"
        return dest_path, original_name, size_bytes, mime_type

    @classmethod
    def _extract_or_fail(cls, file_path: str, mime_type: str, file_name: str) -> str:
        """Extract text; prefer data_engineering extractors; hard-fail on empty/corrupt."""
        try:
            with open(file_path, "rb") as fh:
                file_bytes = fh.read()
            from app.services.de_bridge import extract_text_from_bytes

            return extract_text_from_bytes(file_bytes, file_name)
        except Exception as de_exc:
            logger.info("DE extraction fallback (%s): %s", file_name, de_exc)
            try:
                text = DocumentExtractor.extract_text_from_file(file_path, mime_type)
            except Exception as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to extract text from upload: {exc}",
                ) from exc
            if not (text or "").strip():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Document yielded no extractable text.",
                )
            return text

    @classmethod
    def _notify_officers_of_submission(
        cls, db: Session, doc: Document, actor: User, is_revision: bool = False
    ) -> None:
        officers = db.query(User).filter(User.role == UserRole.OFFICER).all()
        verb = "resubmitted" if is_revision else "submitted"
        for officer in officers:
            NotificationService.create_notification(
                db=db,
                user_id=officer.id,
                document_id=doc.id,
                title=f"New document {verb}: {doc.title}",
                message=(
                    f"Advisor {actor.full_name} {verb} '{doc.title}' "
                    f"(v{doc.version_number}) for compliance review."
                ),
            )

    @classmethod
    def _run_analysis_safe(cls, db: Session, doc: Document) -> None:
        try:
            result = AIAssistService.generate_or_get_analysis(db, doc)
            model_used = (
                (result or {}).get("model_used")
                or (result or {}).get("status")
                or "unknown"
            )
            AuditService.log_event(
                db=db,
                document_id=doc.id,
                action=AuditAction.ANALYSIS_GENERATED,
                actor=None,
                details={
                    "model": model_used,
                    "status": (result or {}).get("status"),
                },
            )
            # Optional full DE ingest into pgvector chunk tables
            try:
                from app.services.de_bridge import try_ingest_document

                with open(doc.file_path, "rb") as fh:
                    try_ingest_document(doc.id, fh.read(), doc.file_name)
            except Exception as ingest_exc:
                logger.warning("DE ingest skipped/failed: %s", ingest_exc)
        except Exception as exc:
            logger.exception("AI analysis failed for document %s: %s", doc.id, exc)

    @classmethod
    def create_document(
        cls,
        db: Session,
        advisor: User,
        title: str,
        document_type: DocumentType,
        file: UploadFile,
    ) -> Document:
        file_path, file_name, file_size, mime_type = cls._save_file(file)
        extracted_text = cls._extract_or_fail(file_path, mime_type, file_name)

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
            version_number=1,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        AuditService.log_event(
            db=db,
            document_id=doc.id,
            action=AuditAction.SUBMITTED,
            actor=advisor,
            details={"title": title, "file_name": file_name, "version": 1},
        )
        cls._notify_officers_of_submission(db, doc, advisor, is_revision=False)
        cls._run_analysis_safe(db, doc)
        return doc

    @classmethod
    def create_revision(
        cls,
        db: Session,
        advisor: User,
        parent_document_id: str,
        title: str,
        document_type: DocumentType,
        file: UploadFile,
    ) -> Document:
        parent = db.query(Document).filter(Document.id == parent_document_id).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent document not found.",
            )

        if parent.advisor_id != advisor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only revise documents you originally submitted.",
            )

        if parent.status != DocumentStatus.NEEDS_REVISION:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Revisions can only be submitted for documents in "
                    f"'{DocumentStatus.NEEDS_REVISION.value}' status. "
                    f"Current status: '{parent.status.value}'."
                ),
            )

        # Prevent duplicate revisions from the same parent leaf
        existing_child = (
            db.query(Document)
            .filter(Document.parent_document_id == parent.id)
            .first()
        )
        if existing_child:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "A revision has already been submitted for this document. "
                    f"Use document id '{existing_child.id}' (v{existing_child.version_number})."
                ),
            )

        file_path, file_name, file_size, mime_type = cls._save_file(file)
        extracted_text = cls._extract_or_fail(file_path, mime_type, file_name)

        # Next version = max in thread + 1 (avoids duplicate version numbers)
        max_version = (
            db.query(Document)
            .filter(Document.thread_id == parent.thread_id)
            .order_by(desc(Document.version_number))
            .first()
        )
        next_version = (max_version.version_number if max_version else parent.version_number) + 1

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
            version_number=next_version,
        )
        db.add(revised_doc)
        # Parent remains needs_revision for history, but duplicate revise is blocked above
        db.commit()
        db.refresh(revised_doc)

        AuditService.log_event(
            db=db,
            document_id=revised_doc.id,
            action=AuditAction.RESUBMITTED,
            actor=advisor,
            details={
                "parent_document_id": parent.id,
                "version": revised_doc.version_number,
                "file_name": file_name,
            },
        )
        cls._notify_officers_of_submission(db, revised_doc, advisor, is_revision=True)
        cls._run_analysis_safe(db, revised_doc)
        return revised_doc

    @classmethod
    def record_decision(
        cls,
        db: Session,
        officer: User,
        document_id: str,
        decision_status: DocumentStatus,
        comment: str,
    ) -> Tuple[Document, ReviewDecision]:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found.",
            )

        if decision_status == DocumentStatus.PENDING_REVIEW:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Decision status cannot be 'pending_review'. "
                    "Choose 'approved', 'rejected', or 'needs_revision'."
                ),
            )

        if doc.status != DocumentStatus.PENDING_REVIEW:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Document is not awaiting review (current status: '{doc.status.value}'). "
                    "Only documents in 'pending_review' can receive a decision."
                ),
            )

        # Superseded parents that already have a child should not be re-decided
        child = db.query(Document).filter(Document.parent_document_id == doc.id).first()
        if child:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This document has been superseded by a revision and cannot be decided.",
            )

        doc.status = decision_status
        review_record = ReviewDecision(
            document_id=doc.id,
            officer_id=officer.id,
            status=decision_status,
            comment=comment,
        )
        db.add(review_record)
        db.commit()
        db.refresh(doc)
        db.refresh(review_record)

        AuditService.log_event(
            db=db,
            document_id=doc.id,
            action=AuditAction.DECIDED,
            actor=officer,
            details={"decision": decision_status.value, "comment": comment},
        )

        status_label = decision_status.value.replace("_", " ").title()
        NotificationService.create_notification(
            db=db,
            user_id=doc.advisor_id,
            document_id=doc.id,
            title=f"Document {status_label}: {doc.title}",
            message=(
                f"Compliance Officer {officer.full_name} marked version {doc.version_number} "
                f"as '{status_label}'. Comment: \"{comment}\""
            ),
        )

        try:
            raw_text = doc.extracted_text or ""
            masked_text, _ = PIIMasker.mask_text(
                raw_text, document_id=doc.id, db=db, replace_mappings=False
            )
            VectorEngine.index_reviewed_document_as_precedent(
                db=db,
                document_id=doc.id,
                title=doc.title,
                document_type=doc.document_type,
                masked_text=masked_text,
                decision=decision_status,
                officer_comment=comment,
            )
        except Exception as exc:
            logger.exception("Precedent indexing failed for %s: %s", doc.id, exc)

        return doc, review_record

    @classmethod
    def get_documents_for_user(
        cls,
        db: Session,
        user: User,
        status_filter: Optional[str] = None,
    ) -> List[Document]:
        query = db.query(Document)

        if user.role == UserRole.ADVISOR:
            query = query.filter(Document.advisor_id == user.id)

        if status_filter and status_filter.lower() != "all":
            try:
                s_enum = DocumentStatus(status_filter.lower())
                query = query.filter(Document.status == s_enum)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter '{status_filter}'.",
                ) from exc

        return query.order_by(desc(Document.uploaded_at)).all()

    @classmethod
    def get_document_by_id(
        cls,
        db: Session,
        document_id: str,
        user: User,
        log_view: bool = True,
    ) -> Document:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found.",
            )

        if user.role == UserRole.ADVISOR and doc.advisor_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view this document.",
            )

        if log_view:
            AuditService.log_event(
                db=db,
                document_id=doc.id,
                action=AuditAction.VIEWED,
                actor=user,
                details={"viewer_role": user.role.value},
            )

        return doc

    @classmethod
    def get_document_thread(
        cls,
        db: Session,
        document_id: str,
        user: User,
    ) -> Tuple[str, List[Document]]:
        current_doc = cls.get_document_by_id(db, document_id, user, log_view=False)
        thread_docs = (
            db.query(Document)
            .filter(Document.thread_id == current_doc.thread_id)
            .order_by(Document.version_number.asc())
            .all()
        )
        return current_doc.thread_id, thread_docs

    @staticmethod
    def attach_latest_decision(doc: Document) -> Document:
        decisions = list(doc.review_decisions or [])
        if decisions:
            # relationship ordered desc by decided_at
            doc.latest_decision = decisions[0]  # type: ignore[attr-defined]
        else:
            doc.latest_decision = None  # type: ignore[attr-defined]
        return doc
