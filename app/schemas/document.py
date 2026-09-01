from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.models.base import DocumentStatus, DocumentType
from app.schemas.user import UserOut
from app.schemas.review import ReviewDecisionOut
from app.schemas.ai_analysis import AIAnalysisOut

class DocumentBase(BaseModel):
    title: str
    document_type: DocumentType = DocumentType.OTHER

class DocumentListItemOut(DocumentBase):
    id: str
    advisor_id: str
    status: DocumentStatus
    file_name: str
    file_size: int
    mime_type: str
    thread_id: str
    parent_document_id: Optional[str] = None
    version_number: int
    uploaded_at: datetime
    updated_at: datetime
    advisor: Optional[UserOut] = None
    latest_decision: Optional[ReviewDecisionOut] = None

    model_config = ConfigDict(from_attributes=True)

class DocumentDetailOut(DocumentListItemOut):
    extracted_text: Optional[str] = None
    review_decisions: List[ReviewDecisionOut] = []
    ai_analysis: Optional[AIAnalysisOut] = None

    model_config = ConfigDict(from_attributes=True)

class DocumentThreadOut(BaseModel):
    thread_id: str
    total_versions: int
    current_version: int
    documents: List[DocumentDetailOut]

class DocumentCreateResponse(BaseModel):
    document: DocumentDetailOut
    message: str = "Document successfully uploaded and queued for review"
