from datetime import datetime, timezone
import enum
from sqlalchemy import Column, String, Integer, BigInteger, Boolean, DateTime, Enum, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class PaymentMethod(str, enum.Enum):
    UPI = "UPI"
    CARD = "CARD"
    NEFT = "NEFT"
    RTGS = "RTGS"


class PaymentStatus(str, enum.Enum):
    CREATED = "CREATED"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    DECLINED = "DECLINED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, index=True)
    customer_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    merchant_id = Column(String(36), ForeignKey("merchants.id", ondelete="RESTRICT"), nullable=False, index=True)
    payment_method = Column(Enum(PaymentMethod), nullable=False, index=True)
    
    # Financial fields in integer paise
    amount_paise = Column(BigInteger, nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    
    # Fee snapshot (immutable after initiation/processing)
    fee_bps_snapshot = Column(Integer, default=0, nullable=False)
    fee_flat_paise_snapshot = Column(Integer, default=0, nullable=False)
    calculated_fee_paise = Column(BigInteger, default=0, nullable=False)
    
    status = Column(Enum(PaymentStatus), default=PaymentStatus.CREATED, nullable=False, index=True)
    
    merchant_order_ref = Column(String(100), nullable=True)
    idempotency_key = Column(String(100), nullable=True, index=True)
    instrument_ref = Column(String(100), nullable=True)
    
    # Bank reference given by simulated bank
    bank_reference = Column(String(100), nullable=True, index=True)
    
    # Scenario and error fields
    active_scenario = Column(String(50), nullable=True)
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Settlement & refund flags
    settled_item_id = Column(String(36), nullable=True)
    total_refunded_paise = Column(BigInteger, default=0, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    customer = relationship("User", back_populates="payments")
    merchant = relationship("Merchant", back_populates="payments")
    attempts = relationship("PaymentAttempt", back_populates="payment", cascade="all, delete-orphan")
    events = relationship("PaymentEvent", back_populates="payment", cascade="all, delete-orphan", order_by="PaymentEvent.created_at")
    holds = relationship("BalanceHold", back_populates="payment")
    refunds = relationship("Refund", back_populates="payment")
    bank_transactions = relationship("BankTransaction", back_populates="payment")
    risk_decisions = relationship("RiskDecision", back_populates="payment")


class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"

    id = Column(String(36), primary_key=True, index=True)
    payment_id = Column(String(36), ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, index=True)
    attempt_number = Column(Integer, default=1, nullable=False)
    route_id = Column(String(36), ForeignKey("payment_routes.id", ondelete="SET NULL"), nullable=True)
    bank_id = Column(String(36), ForeignKey("simulated_banks.id", ondelete="RESTRICT"), nullable=False)
    
    status = Column(String(50), nullable=False)
    request_payload = Column(Text, nullable=True)
    response_payload = Column(Text, nullable=True)
    bank_reference = Column(String(100), nullable=True)
    latency_ms = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    payment = relationship("Payment", back_populates="attempts")
    bank = relationship("SimulatedBank")


class PaymentEvent(Base):
    __tablename__ = "payment_events"

    id = Column(String(36), primary_key=True, index=True)
    payment_id = Column(String(36), ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    from_status = Column(String(50), nullable=True)
    to_status = Column(String(50), nullable=False)
    correlation_id = Column(String(100), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    payment = relationship("Payment", back_populates="events")


class PaymentRoute(Base):
    __tablename__ = "payment_routes"

    id = Column(String(36), primary_key=True, index=True)
    payment_method = Column(Enum(PaymentMethod), nullable=False, index=True)
    bank_id = Column(String(36), ForeignKey("simulated_banks.id", ondelete="CASCADE"), nullable=False, index=True)
    is_enabled = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=1, nullable=False)
    fee_bps = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    bank = relationship("SimulatedBank", back_populates="routes")


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    id = Column(String(36), primary_key=True, index=True)
    actor_id = Column(String(36), nullable=False, index=True)
    operation = Column(String(50), nullable=False, index=True)
    idempotency_key = Column(String(100), nullable=False, index=True)
    request_hash = Column(String(64), nullable=False)
    
    response_status = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    payment_id = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("actor_id", "operation", "idempotency_key", name="uq_actor_op_idempotency"),
    )
