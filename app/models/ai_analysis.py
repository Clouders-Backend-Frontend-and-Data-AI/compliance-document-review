from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base
from app.models.base import FlagSeverity

class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, unique=True, index=True)
    summary = Column(Text, nullable=False)
    outbound_payload_masked = Column(Text, nullable=True)  # Snapshot of payload sent to AI to verify PII masking
    status = Column(String(50), default="completed", nullable=False)  # completed, degraded, failed
    model_used = Column(String(100), default="gemini-1.5-flash", nullable=False)
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    document = relationship("Document", back_populates="ai_analysis", foreign_keys=[document_id])
    flags = relationship("ComplianceFlag", back_populates="analysis", cascade="all, delete-orphan")

class ComplianceFlag(Base):
    __tablename__ = "compliance_flags"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String(36), ForeignKey("ai_analyses.id"), nullable=False, index=True)
    passage_excerpt = Column(Text, nullable=False)
    matched_rule_id = Column(String(100), nullable=True)
    matched_rule_title = Column(String(255), nullable=True)
    matched_rule_text = Column(Text, nullable=True)
    explanation = Column(Text, nullable=False)
    severity = Column(SQLEnum(FlagSeverity), default=FlagSeverity.MEDIUM, nullable=False)
    suggested_fix = Column(Text, nullable=True)

    # Relationships
    analysis = relationship("AIAnalysis", back_populates="flags", foreign_keys=[analysis_id])
