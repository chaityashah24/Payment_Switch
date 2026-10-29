from datetime import datetime, timezone
from sqlalchemy import Column, String, BigInteger, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    id = Column(String(36), primary_key=True, index=True)
    bank_id = Column(String(36), ForeignKey("simulated_banks.id", ondelete="RESTRICT"), nullable=False, index=True)
    payment_id = Column(String(36), ForeignKey("payments.id", ondelete="SET NULL"), nullable=True, index=True)
    bank_reference = Column(String(100), unique=True, nullable=False, index=True)
    
    customer_account_id = Column(String(36), ForeignKey("simulated_accounts.id", ondelete="RESTRICT"), nullable=True)
    merchant_account_id = Column(String(36), ForeignKey("simulated_accounts.id", ondelete="RESTRICT"), nullable=True)
    
    amount_paise = Column(BigInteger, nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    
    transaction_type = Column(String(50), nullable=False)  # DEBIT, CREDIT, REVERSAL
    status = Column(String(50), nullable=False)  # SUCCESS, DECLINED, PENDING, FAILED
    
    scenario_applied = Column(String(50), nullable=True)
    raw_payload = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    bank = relationship("SimulatedBank", back_populates="transactions")
    payment = relationship("Payment", back_populates="bank_transactions")
    events = relationship("BankEvent", back_populates="bank_transaction", cascade="all, delete-orphan")


class BankEvent(Base):
    __tablename__ = "bank_events"

    id = Column(String(36), primary_key=True, index=True)
    bank_transaction_id = Column(String(36), ForeignKey("bank_transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    event_data = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    bank_transaction = relationship("BankTransaction", back_populates="events")
