from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_officer
from app.models.base import RuleCategory
from app.models.user import User
from app.models.vector_corpus import ComplianceRule, PrecedentSubmission
from app.schemas.vector_corpus import ComplianceRuleOut, PrecedentOut

router = APIRouter(prefix="/corpus", tags=["Compliance Corpus & Knowledge Base"])


@router.get("/rules", response_model=List[ComplianceRuleOut])
def get_compliance_rules(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Browse the indexed compliance rules and mandatory disclosure catalogue."""
    query = db.query(ComplianceRule)
    if category:
        try:
            cat_enum = RuleCategory(category)
            query = query.filter(ComplianceRule.category == cat_enum)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category '{category}'.",
            ) from exc
    return query.order_by(ComplianceRule.rule_code.asc()).all()


@router.get("/precedents", response_model=List[PrecedentOut])
def get_precedent_submissions(
    limit: int = Query(50, le=100),
    current_user: User = Depends(require_officer),
    db: Session = Depends(get_db),
):
    """Browse past reviewed submissions and precedent decisions (officers only)."""
    return (
        db.query(PrecedentSubmission)
        .order_by(PrecedentSubmission.created_at.desc())
        .limit(limit)
        .all()
    )
