from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.models.base import DocumentStatus
from app.schemas.user import UserOut

class ReviewDecisionCreate(BaseModel):
    status: DocumentStatus = Field(..., description="Decision outcome: approved, rejected, or needs_revision")
    comment: str = Field(..., min_length=3, description="Officer's review explanation and feedback")

class ReviewDecisionOut(BaseModel):
    id: str
    document_id: str
    officer_id: str
    status: DocumentStatus
    comment: str
    decided_at: datetime
    officer: Optional[UserOut] = None

    model_config = ConfigDict(from_attributes=True)
