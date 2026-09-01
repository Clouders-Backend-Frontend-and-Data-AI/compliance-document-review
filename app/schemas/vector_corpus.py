from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.base import RuleCategory, DocumentStatus, DocumentType

class ComplianceRuleOut(BaseModel):
    id: str
    rule_code: str
    category: RuleCategory
    title: str
    description: str
    rule_text: str
    standard_disclosure: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PrecedentOut(BaseModel):
    id: str
    title: str
    document_type: DocumentType
    masked_text: str
    decision: DocumentStatus
    officer_comment: str
    source_document_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
