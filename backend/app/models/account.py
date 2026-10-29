from datetime import datetime, timezone
import enum
from sqlalchemy import Column, String, Integer, BigInteger, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class InstrumentType(str, enum.Enum):
    UPI_VPA = "UPI_VPA"
    CARD_TOKEN = "CARD_TOKEN"
    BANK_ACCOUNT = "BANK_ACCOUNT"


class HoldStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    CAPTURED = "CAPTURED"
    RELEASED = "RELEASED"


class SimulatedBank(Base):
    __tablename__ = "simulated_banks"

    id = Column(String(36), primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)  # e.g. "SIM_HDFC", "SIM_ICICI"
    name = Column(String(100), nullable=False)
    ifsc_prefix = Column(String(10), nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    latency_ms = Column(Integer, default=50, nullable=False)
    downtime_until = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    accounts = relationship("SimulatedAccount", back_populates="bank")
    routes = relationship("PaymentRoute", back_populates="bank")
    transactions = relationship("BankTransaction", back_populates="bank")


class SimulatedAccount(Base):
    __tablename__ = "simulated_accounts"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    bank_id = Column(String(36), ForeignKey("simulated_banks.id", ondelete="RESTRICT"), nullable=False, index=True)
    account_number = Column(String(50), unique=True, nullable=False)
    account_type = Column(String(20), default="SAVINGS", nullable=False)  # SAVINGS, CURRENT
    
    # Balance in integer paise
    balance_paise = Column(BigInteger, default=0, nullable=False)
    available_balance_paise = Column(BigInteger, default=0, nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="simulated_accounts")
    bank = relationship("SimulatedBank", back_populates="accounts")
    holds = relationship("BalanceHold", back_populates="account")


class PaymentInstrument(Base):
    __tablename__ = "payment_instruments"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    bank_id = Column(String(36), ForeignKey("simulated_banks.id", ondelete="RESTRICT"), nullable=True)
    instrument_type = Column(Enum(InstrumentType), nullable=False)
    masked_identifier = Column(String(100), nullable=False)  # e.g., "customer@simupi", "**** 4242"
    token_ref = Column(String(100), unique=True, nullable=False)
    card_brand = Column(String(50), nullable=True)  # VISA, MASTERCARD, RUPAY
    expiry_month = Column(Integer, nullable=True)
    expiry_year = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="payment_instruments")


class BalanceHold(Base):
    __tablename__ = "balance_holds"

    id = Column(String(36), primary_key=True, index=True)
    payment_id = Column(String(36), ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_account_id = Column(String(36), ForeignKey("simulated_accounts.id", ondelete="RESTRICT"), nullable=False, index=True)
    amount_paise = Column(BigInteger, nullable=False)
    status = Column(Enum(HoldStatus), default=HoldStatus.ACTIVE, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    account = relationship("SimulatedAccount", back_populates="holds")
    payment = relationship("Payment", back_populates="holds")
