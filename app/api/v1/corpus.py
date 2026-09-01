from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.vector_corpus import ComplianceRule, PrecedentSubmission
from app.models.base import RuleCategory
from app.schemas.vector_corpus import ComplianceRuleOut, PrecedentOut

router = APIRouter(prefix="/corpus", tags=["Compliance Corpus & Knowledge Base"])

@router.get("/rules", response_model=List[ComplianceRuleOut])
def get_compliance_rules(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Browse the indexed compliance rules and mandatory disclosure catalogue.
    """
    query = db.query(ComplianceRule)
    if category:
        try:
            cat_enum = RuleCategory(category)
            query = query.filter(ComplianceRule.category == cat_enum)
        except ValueError:
            pass
    return query.order_by(ComplianceRule.rule_code.asc()).all()

@router.get("/precedents", response_model=List[PrecedentOut])
def get_precedent_submissions(
    limit: int = Query(50, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Browse past reviewed submissions and precedent decisions in the vector store.
    """
    return db.query(PrecedentSubmission).order_by(PrecedentSubmission.created_at.desc()).limit(limit).all()
