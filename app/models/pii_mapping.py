from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base

class PIIMapping(Base):
    __tablename__ = "pii_mappings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    placeholder = Column(String(100), nullable=False)  # e.g., "[CLIENT_1]", "[EMAIL_1]"
    original_value = Column(Text, nullable=False)      # e.g., "John Doe", "john@example.com"
    entity_type = Column(String(50), nullable=False)   # name, email, phone, address, ssn, account_number, amount
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    document = relationship("Document", back_populates="pii_mappings", foreign_keys=[document_id])
