from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.deps import get_db          
from app.services.ai_assist import AIAssistService
from app.models.document import Document

router = APIRouter()


@router.post("/documents/{document_id}/analyze", response_model=dict)
def regenerate_analysis(
    document_id: str,                      
    force: bool = True,
    db: Session = Depends(get_db),
):
    # Check if document exists
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        analysis = AIAssistService.generate_or_get_analysis(
            document_id=document_id,
            force_regenerate=force,         
            db=db,
        )
        return {
            "status": "success",
            "analysis_id": analysis.id,
            "summary": analysis.summary,
            "flags_count": len(analysis.flags) if analysis.flags else 0,
            "model_used": analysis.model_used,
        }
    except Exception as e:
        # Graceful degradation – returns error state so UI can retry
        return {
            "status": "error",
            "message": str(e),
            "analysis_id": None,
        }