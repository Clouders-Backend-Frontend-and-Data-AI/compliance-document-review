import enum
from app.core.database import Base

class UserRole(str, enum.Enum):
    ADVISOR = "advisor"
    OFFICER = "officer"

class DocumentStatus(str, enum.Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"

class DocumentType(str, enum.Enum):
    MARKETING_EMAIL = "marketing_email"
    BROCHURE = "brochure"
    SOCIAL_POST = "social_post"
    MEETING_NOTES = "meeting_notes"
    PROPOSAL_LETTER = "proposal_letter"
    OTHER = "other"

class AuditAction(str, enum.Enum):
    SUBMITTED = "submitted"
    VIEWED = "viewed"
    DECIDED = "decided"
    RESUBMITTED = "resubmitted"
    ANALYSIS_GENERATED = "analysis_generated"
    DOWNLOADED = "downloaded"

class FlagSeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class RuleCategory(str, enum.Enum):
    REQUIRED_DISCLOSURE = "required_disclosure"
    PROHIBITED_CLAIMS = "prohibited_claims"
    PERFORMANCE_STANDARDS = "performance_standards"
    SUPERVISION = "supervision"
