from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from app.models.merchant import MerchantStatus


class MerchantOnboardingRequest(BaseModel):
    business_name: str = Field(..., min_length=2, max_length=255)
    contact_email: EmailStr
    business_category: str = Field(..., example="E-COMMERCE")
    settlement_account_ref: str = Field(..., example="SIM_HDFC_9876543210")
    supported_methods: Optional[str] = "UPI,CARD,NEFT,RTGS"
    fee_percentage_bps: Optional[int] = Field(default=150, ge=0, le=1000, description="150 = 1.50%")
    fee_flat_paise: Optional[int] = Field(default=0, ge=0, description="Fixed fee in paise")


class MerchantUpdateRequest(BaseModel):
    business_name: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    settlement_account_ref: Optional[str] = None
    supported_methods: Optional[str] = None
    fee_percentage_bps: Optional[int] = None
    fee_flat_paise: Optional[int] = None


class MerchantReviewRequest(BaseModel):
    status: MerchantStatus  # APPROVED, REJECTED, SUSPENDED
    rejection_reason: Optional[str] = None


class MerchantResponse(BaseModel):
    id: str
    business_name: str
    contact_email: str
    business_category: str
    settlement_account_ref: str
    supported_methods: str
    fee_percentage_bps: int
    fee_flat_paise: int
    status: MerchantStatus
    rejection_reason: Optional[str] = None
    created_at: datetime
    approved_at: Optional[datetime] = None

    class Config:
        from_attributes = True
