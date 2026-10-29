from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.account import InstrumentType, HoldStatus


class BankResponse(BaseModel):
    id: str
    code: str
    name: str
    ifsc_prefix: str
    is_available: bool
    latency_ms: int
    downtime_until: Optional[datetime] = None

    class Config:
        from_attributes = True


class SimulatedAccountResponse(BaseModel):
    id: str
    account_number: str
    account_type: str
    balance_paise: int
    available_balance_paise: int
    currency: str
    bank: BankResponse

    class Config:
        from_attributes = True


class PaymentInstrumentCreate(BaseModel):
    instrument_type: InstrumentType
    identifier: str  # e.g. "customer@okaxis" or "4111111111111111"
    bank_id: Optional[str] = None
    card_brand: Optional[str] = None
    expiry_month: Optional[int] = None
    expiry_year: Optional[int] = None


class PaymentInstrumentResponse(BaseModel):
    id: str
    instrument_type: InstrumentType
    masked_identifier: str
    token_ref: str
    card_brand: Optional[str] = None
    expiry_month: Optional[int] = None
    expiry_year: Optional[int] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class BalanceHoldResponse(BaseModel):
    id: str
    payment_id: str
    amount_paise: int
    status: HoldStatus
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True
