from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Enum as SQLEnum
import uuid
from app.core.database import Base
from app.models.base import RuleCategory, DocumentStatus, DocumentType

class ComplianceRule(Base):
    __tablename__ = "compliance_rules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_code = Column(String(50), unique=True, index=True, nullable=False) # e.g. "SEC-MKT-01", "FINRA-2210-A"
    category = Column(SQLEnum(RuleCategory), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    rule_text = Column(Text, nullable=False)
    standard_disclosure = Column(Text, nullable=True) # If it's a required disclosure rule
    embedding_json = Column(Text, nullable=True) # JSON list of floats for embedding vector
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

class PrecedentSubmission(Base):
    __tablename__ = "precedent_submissions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    document_type = Column(SQLEnum(DocumentType), default=DocumentType.OTHER, nullable=False)
    masked_text = Column(Text, nullable=False)
    decision = Column(SQLEnum(DocumentStatus), nullable=False) # approved, rejected, needs_revision
    officer_comment = Column(Text, nullable=False)
    source_document_id = Column(String(36), nullable=True)
    embedding_json = Column(Text, nullable=True) # JSON list of floats for embedding vector
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
