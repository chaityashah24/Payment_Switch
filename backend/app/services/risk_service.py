import uuid
from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.risk import RiskRule, RiskDecision, RiskRuleType, RiskAction
from app.models.payment import Payment, PaymentStatus
from app.models.merchant import Merchant, MerchantStatus


def evaluate_risk(
    db: Session,
    customer_id: str,
    merchant: Merchant,
    amount_paise: int,
    payment: Payment,
) -> Tuple[RiskAction, str, Optional[str]]:
    """
    Evaluates active risk rules.
    Returns: (Action, Reason, MatchedRuleId)
    """
    # Rule 0: Merchant status check (Suspended or Rejected merchants cannot accept payments)
    if merchant.status == MerchantStatus.SUSPENDED:
        return RiskAction.DECLINE, "Merchant account is currently SUSPENDED by system administrator", None

    if merchant.status != MerchantStatus.APPROVED:
        return RiskAction.DECLINE, f"Merchant status is '{merchant.status.value}'; only APPROVED merchants can accept payments", None

    active_rules = db.query(RiskRule).filter(RiskRule.is_active == True).all()

    now = datetime.now(timezone.utc)

    for rule in active_rules:
        # 1. MAX_AMOUNT rule
        if rule.rule_type == RiskRuleType.MAX_AMOUNT:
            if amount_paise > rule.threshold_value:
                return rule.action, f"Transaction amount ₹{amount_paise / 100:.2f} exceeds rule limit of ₹{rule.threshold_value / 100:.2f}", rule.id

        # 2. VELOCITY_WINDOW rule (e.g. max 5 attempts in 300 seconds)
        elif rule.rule_type == RiskRuleType.VELOCITY_WINDOW:
            window_start = now - timedelta(seconds=rule.window_seconds)
            recent_attempts = (
                db.query(func.count(Payment.id))
                .filter(
                    Payment.customer_id == customer_id,
                    Payment.created_at >= window_start,
                )
                .scalar()
            )
            if recent_attempts >= rule.threshold_value:
                return rule.action, f"Velocity threshold exceeded: {recent_attempts} payment attempts in last {rule.window_seconds}s", rule.id

        # 3. REPEATED_MERCHANT rule (repeated transactions to same merchant within short window)
        elif rule.rule_type == RiskRuleType.REPEATED_MERCHANT:
            window_start = now - timedelta(seconds=rule.window_seconds)
            same_merchant_count = (
                db.query(func.count(Payment.id))
                .filter(
                    Payment.customer_id == customer_id,
                    Payment.merchant_id == merchant.id,
                    Payment.created_at >= window_start,
                )
                .scalar()
            )
            if same_merchant_count >= rule.threshold_value:
                return rule.action, f"Repeated payment rule triggered: {same_merchant_count} payments to merchant '{merchant.business_name}' in {rule.window_seconds}s", rule.id

    return RiskAction.ALLOW, "Transaction passed all automated risk rules", None


def record_risk_decision(
    db: Session,
    payment_id: str,
    action: RiskAction,
    reason: str,
    rule_id: Optional[str] = None,
) -> RiskDecision:
    decision = RiskDecision(
        id=str(uuid.uuid4()),
        payment_id=payment_id,
        risk_rule_id=rule_id,
        action=action,
        reason=reason,
    )
    db.add(decision)
    db.flush()
    return decision
