import json
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.audit import AuditEvent
from app.models.user import User
from app.models.base import AuditAction

class AuditService:
    """Append-only audit trail logger for compliance actions"""

    @staticmethod
    def log_event(
        db: Session,
        document_id: str,
        action: AuditAction,
        actor: Optional[User] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        details_str = json.dumps(details) if details else None
        event = AuditEvent(
            document_id=document_id,
            actor_id=actor.id if actor else None,
            actor_name=actor.full_name if actor else "System",
            actor_role=actor.role if actor else None,
            action=action,
            details_json=details_str
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def get_document_audit_trail(db: Session, document_id: str):
        return db.query(AuditEvent).filter(
            AuditEvent.document_id == document_id
        ).order_by(AuditEvent.created_at.asc()).all()

    @staticmethod
    def get_thread_audit_trail(db: Session, thread_id: str):
        from app.models.document import Document
        doc_ids = [d.id for d in db.query(Document.id).filter(Document.thread_id == thread_id).all()]
        return db.query(AuditEvent).filter(
            AuditEvent.document_id.in_(doc_ids)
        ).order_by(AuditEvent.created_at.asc()).all()
