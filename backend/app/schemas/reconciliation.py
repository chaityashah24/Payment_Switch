from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.reconciliation import (
    RecRunStatus,
    RecExceptionType,
    RecExceptionSeverity,
    RecExceptionStatus,
)


class RecRunCreateRequest(BaseModel):
    bank_id: Optional[str] = None
    period_start: datetime
    period_end: datetime


class RecExceptionResponse(BaseModel):
    id: str
    reconciliation_run_id: str
    exception_type: RecExceptionType
    severity: RecExceptionSeverity
    status: RecExceptionStatus
    payment_id: Optional[str] = None
    bank_transaction_id: Optional[str] = None
    reference_key: Optional[str] = None
    explanation: str
    resolution_notes: Optional[str] = None
    resolved_by_user_id: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RecRunResponse(BaseModel):
    id: str
    run_reference: str
    bank_id: Optional[str] = None
    period_start: datetime
    period_end: datetime
    status: RecRunStatus
    total_switch_records: int
    total_bank_records: int
    total_matched: int
    total_exceptions: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    exceptions: Optional[List[RecExceptionResponse]] = None

    class Config:
        from_attributes = True


class RecExceptionResolveRequest(BaseModel):
    resolution_notes: str = Field(..., min_length=5, max_length=500)
    mark_as: RecExceptionStatus = Field(default=RecExceptionStatus.RESOLVED)
