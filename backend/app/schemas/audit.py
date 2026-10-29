from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    correlation_id: Optional[str] = None
    ip_address: Optional[str] = None
    changes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
