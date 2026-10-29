from datetime import datetime, timezone
import enum
from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Enum, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class BatchStatus(str, enum.Enum):
    CREATED = "CREATED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIALLY_FAILED = "PARTIALLY_FAILED"


class SettlementItemStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"


class SettlementBatch(Base):
    __tablename__ = "settlement_batches"

    id = Column(String(36), primary_key=True, index=True)
    batch_reference = Column(String(100), unique=True, nullable=False, index=True)
    cutoff_timestamp = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(BatchStatus), default=BatchStatus.CREATED, nullable=False, index=True)
    
    total_gross_paise = Column(BigInteger, default=0, nullable=False)
    total_fee_paise = Column(BigInteger, default=0, nullable=False)
    total_refund_adjustment_paise = Column(BigInteger, default=0, nullable=False)
    total_net_paise = Column(BigInteger, default=0, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    items = relationship("SettlementItem", back_populates="batch", cascade="all, delete-orphan")


class SettlementItem(Base):
    __tablename__ = "settlement_items"

    id = Column(String(36), primary_key=True, index=True)
    settlement_batch_id = Column(String(36), ForeignKey("settlement_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    merchant_id = Column(String(36), ForeignKey("merchants.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    gross_amount_paise = Column(BigInteger, default=0, nullable=False)
    fee_amount_paise = Column(BigInteger, default=0, nullable=False)
    refund_amount_paise = Column(BigInteger, default=0, nullable=False)
    net_payable_paise = Column(BigInteger, default=0, nullable=False)
    
    payout_reference = Column(String(100), unique=True, nullable=True, index=True)
    status = Column(Enum(SettlementItemStatus), default=SettlementItemStatus.PENDING, nullable=False, index=True)
    retry_count = Column(Integer, default=0, nullable=False)
    last_error = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    batch = relationship("SettlementBatch", back_populates="items")
    merchant = relationship("Merchant", back_populates="settlement_items")
    allocations = relationship("SettlementAllocation", back_populates="settlement_item", cascade="all, delete-orphan")


class SettlementAllocation(Base):
    __tablename__ = "settlement_allocations"

    id = Column(String(36), primary_key=True, index=True)
    settlement_item_id = Column(String(36), ForeignKey("settlement_items.id", ondelete="CASCADE"), nullable=False, index=True)
    payment_id = Column(String(36), ForeignKey("payments.id", ondelete="RESTRICT"), nullable=True, index=True)
    refund_id = Column(String(36), ForeignKey("refunds.id", ondelete="RESTRICT"), nullable=True, index=True)
    
    allocation_type = Column(String(20), nullable=False)  # PAYMENT, REFUND
    amount_paise = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    settlement_item = relationship("SettlementItem", back_populates="allocations")
