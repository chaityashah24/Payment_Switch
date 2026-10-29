from datetime import datetime, timezone
import enum
from sqlalchemy import Column, String, BigInteger, DateTime, Enum, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class AccountClassification(str, enum.Enum):
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"


class PostingDirection(str, enum.Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


class JournalEntryType(str, enum.Enum):
    PAYMENT_CAPTURE = "PAYMENT_CAPTURE"
    PAYMENT_HOLD = "PAYMENT_HOLD"
    PAYMENT_RELEASE = "PAYMENT_RELEASE"
    REFUND = "REFUND"
    SETTLEMENT_PAYOUT = "SETTLEMENT_PAYOUT"
    OPENING_BALANCE = "OPENING_BALANCE"
    FEE_ADJUSTMENT = "FEE_ADJUSTMENT"


class LedgerAccount(Base):
    __tablename__ = "ledger_accounts"

    id = Column(String(36), primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)  # e.g., "CUSTOMER_FUNDS_HOLD", "MERCHANT_PAYABLE_M1"
    name = Column(String(100), nullable=False)
    classification = Column(Enum(AccountClassification), nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    
    # Materialized balance in integer paise (updated atomically with postings)
    balance_paise = Column(BigInteger, default=0, nullable=False)
    
    owner_type = Column(String(50), default="SYSTEM", nullable=False)  # SYSTEM, MERCHANT, CUSTOMER
    owner_id = Column(String(36), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    lines = relationship("JournalLine", back_populates="account")


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(String(36), primary_key=True, index=True)
    entry_number = Column(String(100), unique=True, nullable=False, index=True)
    entry_type = Column(Enum(JournalEntryType), nullable=False, index=True)
    source_type = Column(String(50), nullable=False)  # PAYMENT, REFUND, SETTLEMENT_ITEM, SEED
    source_id = Column(String(36), nullable=False, index=True)
    
    description = Column(Text, nullable=False)
    status = Column(String(20), default="POSTED", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    lines = relationship("JournalLine", back_populates="entry", cascade="all, delete-orphan")


class JournalLine(Base):
    __tablename__ = "journal_lines"

    id = Column(String(36), primary_key=True, index=True)
    journal_entry_id = Column(String(36), ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False, index=True)
    ledger_account_id = Column(String(36), ForeignKey("ledger_accounts.id", ondelete="RESTRICT"), nullable=False, index=True)
    direction = Column(Enum(PostingDirection), nullable=False)
    amount_paise = Column(BigInteger, nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("LedgerAccount", back_populates="lines")
