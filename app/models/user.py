from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base
from app.models.base import UserRole

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    documents = relationship("Document", back_populates="advisor", foreign_keys="Document.advisor_id")
    reviews = relationship("ReviewDecision", back_populates="officer", foreign_keys="ReviewDecision.officer_id")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
