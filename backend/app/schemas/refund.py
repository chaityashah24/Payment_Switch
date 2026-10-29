from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.refund import RefundStatus


class RefundCreateRequest(BaseModel):
    payment_id: str
    amount_paise: int = Field(..., gt=0, description="Refund amount in integer paise")
    reason: str = Field(..., min_length=3, max_length=255)
    idempotency_key: str = Field(..., min_length=8, max_length=100)


class RefundResponse(BaseModel):
    id: str
    payment_id: str
    merchant_id: str
    amount_paise: int
    fee_refund_paise: int
    currency: str
    reason: str
    idempotency_key: str
    status: RefundStatus
    bank_reference: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
