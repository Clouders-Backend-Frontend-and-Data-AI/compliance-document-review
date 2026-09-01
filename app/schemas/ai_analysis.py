from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.models.base import FlagSeverity

class ComplianceFlagBase(BaseModel):
    passage_excerpt: str
    matched_rule_id: Optional[str] = None
    matched_rule_title: Optional[str] = None
    matched_rule_text: Optional[str] = None
    explanation: str
    severity: FlagSeverity = FlagSeverity.MEDIUM
    suggested_fix: Optional[str] = None

class ComplianceFlagOut(ComplianceFlagBase):
    id: str
    analysis_id: str

    model_config = ConfigDict(from_attributes=True)

class PrecedentMatchOut(BaseModel):
    id: str
    title: str
    document_type: str
    masked_text_snippet: str
    decision: str
    officer_comment: str
    similarity_score: float

class AIAnalysisOut(BaseModel):
    id: str
    document_id: str
    summary: str
    status: str
    model_used: str
    generated_at: datetime
    flags: List[ComplianceFlagOut] = []
    precedent_matches: List[PrecedentMatchOut] = []

    model_config = ConfigDict(from_attributes=True)

class OutboundPayloadOut(BaseModel):
    document_id: str
    masked_payload: str
    pii_entities_masked_count: int
    note: str = "This shows the exact server-side masked text payload dispatched to external LLM / embedding endpoints. Zero original PII leaves the app perimeter."
