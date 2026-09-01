from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base
from app.models.base import DocumentStatus

class ReviewDecision(Base):
    __tablename__ = "review_decisions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    officer_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # Must be approved, rejected, or needs_revision
    status = Column(SQLEnum(DocumentStatus), nullable=False)
    comment = Column(Text, nullable=False)
    decided_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    document = relationship("Document", back_populates="review_decisions", foreign_keys=[document_id])
    officer = relationship("User", back_populates="reviews", foreign_keys=[officer_id])
