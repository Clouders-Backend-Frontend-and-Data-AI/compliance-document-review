from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base
from app.models.base import AuditAction, UserRole

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(
        String(36),
        ForeignKey("documents.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    actor_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    actor_name = Column(String(255), nullable=True)
    actor_role = Column(SQLEnum(UserRole), nullable=True)
    action = Column(SQLEnum(AuditAction), nullable=False)
    details_json = Column(Text, nullable=True)  # JSON-encoded extra event metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relationships
    document = relationship("Document", back_populates="audit_events", foreign_keys=[document_id])
    actor = relationship("User", foreign_keys=[actor_id])
