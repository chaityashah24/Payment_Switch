import json
import uuid
from typing import Optional, Any
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.core.correlation import get_correlation_id
from app.core.security import redact_sensitive_data


def log_audit_event(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    changes: Optional[Any] = None,
) -> AuditLog:
    serialized_changes = None
    if changes is not None:
        safe_changes = redact_sensitive_data(changes)
        if isinstance(safe_changes, (dict, list)):
            serialized_changes = json.dumps(safe_changes)
        else:
            serialized_changes = str(safe_changes)

    log_entry = AuditLog(
        id=str(uuid.uuid4()),
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        correlation_id=get_correlation_id(),
        ip_address=ip_address,
        changes=serialized_changes,
    )
    db.add(log_entry)
    db.flush()
    return log_entry
