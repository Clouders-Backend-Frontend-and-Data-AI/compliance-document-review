from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, ConfigDict
from app.models.base import AuditAction, UserRole

class AuditEventOut(BaseModel):
    id: str
    document_id: str
    actor_id: Optional[str] = None
    actor_name: Optional[str] = None
    actor_role: Optional[UserRole] = None
    action: AuditAction
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
