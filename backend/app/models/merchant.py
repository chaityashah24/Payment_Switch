from datetime import datetime, timezone
import enum
from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class MerchantStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SUSPENDED = "SUSPENDED"


class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(String(36), primary_key=True, index=True)
    business_name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=False)
    business_category = Column(String(100), nullable=False)  # e.g. E-COMMERCE, RETAIL, UTILITIES
    settlement_account_ref = Column(String(100), nullable=False)
    supported_methods = Column(String(255), default="UPI,CARD,NEFT,RTGS", nullable=False)
    
    # Fees: fee_percentage_bps (basis points: 150 = 1.50%) and fee_flat_paise (e.g. 500 paise = ₹5.00)
    fee_percentage_bps = Column(Integer, default=150, nullable=False)
    fee_flat_paise = Column(Integer, default=0, nullable=False)
    
    status = Column(Enum(MerchantStatus), default=MerchantStatus.PENDING, nullable=False, index=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    memberships = relationship("MerchantMembership", back_populates="merchant", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="merchant")
    refunds = relationship("Refund", back_populates="merchant")
    settlement_items = relationship("SettlementItem", back_populates="merchant")


class MerchantMembership(Base):
    __tablename__ = "merchant_memberships"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    merchant_id = Column(String(36), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    role_in_merchant = Column(String(50), default="OWNER", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "merchant_id", name="uq_user_merchant"),
    )

    user = relationship("User", back_populates="merchant_memberships")
    merchant = relationship("Merchant", back_populates="memberships")
