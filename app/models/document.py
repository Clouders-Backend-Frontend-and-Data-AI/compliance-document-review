from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship, backref
import uuid
from app.core.database import Base
from app.models.base import DocumentStatus, DocumentType

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    advisor_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    document_type = Column(SQLEnum(DocumentType), default=DocumentType.OTHER, nullable=False)
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.PENDING_REVIEW, nullable=False, index=True)
    
    # File Metadata
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    extracted_text = Column(Text, nullable=True)

    # Threading & Revision Linking
    thread_id = Column(String(36), nullable=False, index=True, default=lambda: str(uuid.uuid4()))
    parent_document_id = Column(String(36), ForeignKey("documents.id"), nullable=True, index=True)
    version_number = Column(Integer, default=1, nullable=False)

    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    advisor = relationship("User", back_populates="documents", foreign_keys=[advisor_id])
    parent_document = relationship(
        "Document",
        remote_side=[id],
        foreign_keys=[parent_document_id],
        backref=backref("revisions", order_by="Document.version_number")
    )
    
    review_decisions = relationship("ReviewDecision", back_populates="document", cascade="all, delete-orphan", order_by="desc(ReviewDecision.decided_at)")
    ai_analysis = relationship("AIAnalysis", back_populates="document", uselist=False, cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="document", cascade="all, delete-orphan", order_by="asc(AuditEvent.created_at)")
    pii_mappings = relationship("PIIMapping", back_populates="document", cascade="all, delete-orphan")
