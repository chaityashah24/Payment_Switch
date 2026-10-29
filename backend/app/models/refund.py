from datetime import datetime, timezone
import enum
from sqlalchemy import Column, String, BigInteger, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class RefundStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class Refund(Base):
    __tablename__ = "refunds"

    id = Column(String(36), primary_key=True, index=True)
    payment_id = Column(String(36), ForeignKey("payments.id", ondelete="RESTRICT"), nullable=False, index=True)
    merchant_id = Column(String(36), ForeignKey("merchants.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    amount_paise = Column(BigInteger, nullable=False)
    fee_refund_paise = Column(BigInteger, default=0, nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    
    reason = Column(String(255), nullable=False)
    idempotency_key = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(Enum(RefundStatus), default=RefundStatus.PENDING, nullable=False, index=True)
    
    bank_reference = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    payment = relationship("Payment", back_populates="refunds")
    merchant = relationship("Merchant", back_populates="refunds")
