from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field
from app.models.payment import PaymentMethod, PaymentStatus


class PaymentInitiateRequest(BaseModel):
    merchant_id: str
    payment_method: PaymentMethod
    amount_paise: int = Field(..., gt=0, description="Amount in integer paise (e.g. 10000 = ₹100.00)")
    currency: Optional[str] = "INR"
    instrument_ref: str = Field(..., description="Token reference or identifier for simulated instrument")
    merchant_order_ref: Optional[str] = None
    idempotency_key: str = Field(..., min_length=8, max_length=100)
    demo_auth_token: Optional[str] = None  # e.g. "PIN_1234", "OTP_654321", "3DS_SUCCESS"


class DemoAuthRequest(BaseModel):
    payment_id: str
    auth_credential: str = Field(..., description="Simulated UPI PIN or OTP or Card 3DS Token")


class PaymentEventResponse(BaseModel):
    id: str
    event_type: str
    from_status: Optional[str] = None
    to_status: str
    correlation_id: Optional[str] = None
    details: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentResponse(BaseModel):
    id: str
    customer_id: str
    merchant_id: str
    merchant_name: Optional[str] = None
    payment_method: PaymentMethod
    amount_paise: int
    currency: str
    status: PaymentStatus
    fee_bps_snapshot: int
    fee_flat_paise_snapshot: int
    calculated_fee_paise: int
    net_merchant_paise: int
    merchant_order_ref: Optional[str] = None
    idempotency_key: Optional[str] = None
    instrument_ref: Optional[str] = None
    bank_reference: Optional[str] = None
    active_scenario: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    settled_item_id: Optional[str] = None
    total_refunded_paise: int
    created_at: datetime
    updated_at: datetime
    events: Optional[List[PaymentEventResponse]] = None

    class Config:
        from_attributes = True


class ReceiptResponse(BaseModel):
    payment_id: str
    receipt_number: str
    merchant_name: str
    customer_name: str
    amount_paise: int
    amount_inr: str
    currency: str
    payment_method: str
    status: str
    bank_reference: Optional[str] = None
    timestamp: datetime
    disclaimer: str = "SIMULATION ONLY: This receipt is for educational purposes and represents no real financial transfer."
