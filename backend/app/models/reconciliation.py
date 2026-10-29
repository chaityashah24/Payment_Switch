from datetime import datetime, timezone
import enum
from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class RecRunStatus(str, enum.Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class RecExceptionType(str, enum.Enum):
    MISSING_BANK_RECORD = "MISSING_BANK_RECORD"
    MISSING_SWITCH_RECORD = "MISSING_SWITCH_RECORD"
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    STATUS_MISMATCH = "STATUS_MISMATCH"
    DUPLICATE_EXTERNAL_RECORD = "DUPLICATE_EXTERNAL_RECORD"
    MISSING_LEDGER_POSTING = "MISSING_LEDGER_POSTING"
    INCORRECT_LEDGER_AMOUNT = "INCORRECT_LEDGER_AMOUNT"
    PAYOUT_MISMATCH = "PAYOUT_MISMATCH"


class RecExceptionSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RecExceptionStatus(str, enum.Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"


class ReconciliationRun(Base):
    __tablename__ = "reconciliation_runs"

    id = Column(String(36), primary_key=True, index=True)
    run_reference = Column(String(100), unique=True, nullable=False, index=True)
    bank_id = Column(String(36), ForeignKey("simulated_banks.id", ondelete="SET NULL"), nullable=True)
    
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(RecRunStatus), default=RecRunStatus.IN_PROGRESS, nullable=False, index=True)
    
    total_switch_records = Column(Integer, default=0, nullable=False)
    total_bank_records = Column(Integer, default=0, nullable=False)
    total_matched = Column(Integer, default=0, nullable=False)
    total_exceptions = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    bank = relationship("SimulatedBank")
    exceptions = relationship("ReconciliationException", back_populates="run", cascade="all, delete-orphan")


class ReconciliationException(Base):
    __tablename__ = "reconciliation_exceptions"

    id = Column(String(36), primary_key=True, index=True)
    reconciliation_run_id = Column(String(36), ForeignKey("reconciliation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    exception_type = Column(Enum(RecExceptionType), nullable=False, index=True)
    severity = Column(Enum(RecExceptionSeverity), default=RecExceptionSeverity.HIGH, nullable=False)
    status = Column(Enum(RecExceptionStatus), default=RecExceptionStatus.OPEN, nullable=False, index=True)
    
    payment_id = Column(String(36), ForeignKey("payments.id", ondelete="SET NULL"), nullable=True, index=True)
    bank_transaction_id = Column(String(36), ForeignKey("bank_transactions.id", ondelete="SET NULL"), nullable=True, index=True)
    
    reference_key = Column(String(100), nullable=True, index=True)
    explanation = Column(Text, nullable=False)
    resolution_notes = Column(Text, nullable=True)
    resolved_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    run = relationship("ReconciliationRun", back_populates="exceptions")
    payment = relationship("Payment")
    bank_transaction = relationship("BankTransaction")
    resolved_by = relationship("User")
