from datetime import datetime, timezone
import enum
from sqlalchemy import Column, String, Integer, BigInteger, Boolean, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class RiskRuleType(str, enum.Enum):
    MAX_AMOUNT = "MAX_AMOUNT"
    VELOCITY_WINDOW = "VELOCITY_WINDOW"
    REPEATED_MERCHANT = "REPEATED_MERCHANT"
    FAILED_AUTH_COUNT = "FAILED_AUTH_COUNT"
    SUSPENDED_MERCHANT = "SUSPENDED_MERCHANT"


class RiskAction(str, enum.Enum):
    ALLOW = "ALLOW"
    DECLINE = "DECLINE"
    REVIEW = "REVIEW"


class RiskRule(Base):
    __tablename__ = "risk_rules"

    id = Column(String(36), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=False)
    rule_type = Column(Enum(RiskRuleType), nullable=False, index=True)
    
    threshold_value = Column(BigInteger, nullable=False)  # paise or count
    window_seconds = Column(Integer, default=300, nullable=False)
    action = Column(Enum(RiskAction), default=RiskAction.REVIEW, nullable=False)
    
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class RiskDecision(Base):
    __tablename__ = "risk_decisions"

    id = Column(String(36), primary_key=True, index=True)
    payment_id = Column(String(36), ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, index=True)
    risk_rule_id = Column(String(36), ForeignKey("risk_rules.id", ondelete="SET NULL"), nullable=True)
    
    action = Column(Enum(RiskAction), nullable=False)
    reason = Column(String(255), nullable=False)
    
    resolved_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolution_action = Column(String(50), nullable=True)  # APPROVED_MANUALLY, REJECTED_MANUALLY
    resolution_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    payment = relationship("Payment", back_populates="risk_decisions")
    rule = relationship("RiskRule")
    resolved_by = relationship("User")
