import uuid
from app.models.risk import RiskRule, RiskRuleType, RiskAction
from app.models.payment import PaymentMethod, PaymentStatus
from app.services import risk_service, payment_service


def test_risk_rule_evaluation_and_review(db, test_customer, test_merchant):
    # Create rule: max amount 50000 paise -> REVIEW
    rule = RiskRule(
        id=str(uuid.uuid4()),
        name="Test Max Amount Rule",
        description="Flag payments exceeding ₹500",
        rule_type=RiskRuleType.MAX_AMOUNT,
        threshold_value=50000,
        window_seconds=300,
        action=RiskAction.REVIEW,
        is_active=True,
    )
    db.add(rule)
    db.flush()

    # Initiate payment of ₹800 (80000 paise)
    payment = payment_service.initiate_payment(
        db=db,
        customer=test_customer,
        merchant_id=test_merchant.id,
        payment_method=PaymentMethod.UPI,
        amount_paise=80000,
        instrument_ref="customer@okaxis",
        idempotency_key=f"risk_p_{uuid.uuid4().hex[:8]}",
    )

    assert payment.status == PaymentStatus.PENDING
    assert payment.error_code == "RISK_REVIEW_REQUIRED"
