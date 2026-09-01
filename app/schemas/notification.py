from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class NotificationOut(BaseModel):
    id: str
    user_id: str
    document_id: Optional[str] = None
    title: str
    message: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class NotificationSummary(BaseModel):
    unread_count: int
    notifications: List[NotificationOut]
