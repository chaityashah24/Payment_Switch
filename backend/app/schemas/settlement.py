from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.models.settlement import BatchStatus, SettlementItemStatus


class SettlementPreviewItem(BaseModel):
    merchant_id: str
    merchant_name: str
    eligible_payment_count: int
    gross_amount_paise: int
    fee_amount_paise: int
    eligible_refund_count: int
    refund_amount_paise: int
    net_payable_paise: int


class SettlementPreviewResponse(BaseModel):
    cutoff_timestamp: datetime
    merchants: List[SettlementPreviewItem]
    total_gross_paise: int
    total_fee_paise: int
    total_refund_paise: int
    total_net_payable_paise: int


class SettlementBatchCreateRequest(BaseModel):
    cutoff_timestamp: Optional[datetime] = None  # Defaults to now


class SettlementItemResponse(BaseModel):
    id: str
    merchant_id: str
    merchant_name: Optional[str] = None
    gross_amount_paise: int
    fee_amount_paise: int
    refund_amount_paise: int
    net_payable_paise: int
    payout_reference: Optional[str] = None
    status: SettlementItemStatus
    retry_count: int
    last_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SettlementBatchResponse(BaseModel):
    id: str
    batch_reference: str
    cutoff_timestamp: datetime
    status: BatchStatus
    total_gross_paise: int
    total_fee_paise: int
    total_refund_adjustment_paise: int
    total_net_paise: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    items: Optional[List[SettlementItemResponse]] = None

    class Config:
        from_attributes = True
