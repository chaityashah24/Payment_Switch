import uuid
import pytest
from app.models.payment import PaymentMethod, PaymentStatus
from app.models.refund import RefundStatus
from app.services import payment_service, refund_service
from app.core.exceptions import SwitchException


def test_full_and_partial_refund(db, test_customer, test_merchant):
    amt = 100000  # ₹1,000.00
    p = payment_service.initiate_payment(
        db=db,
        customer=test_customer,
        merchant_id=test_merchant.id,
        payment_method=PaymentMethod.UPI,
        amount_paise=amt,
        instrument_ref="customer@okaxis",
        idempotency_key=f"pay_ref_{uuid.uuid4().hex[:8]}",
    )
    assert p.status == PaymentStatus.SUCCEEDED

    merchant_user = test_merchant.memberships[0].user

    # 1. Partial refund of ₹400 (40000 paise)
    ref1 = refund_service.create_refund(
        db=db,
        merchant_user=merchant_user,
        payment_id=p.id,
        amount_paise=40000,
        reason="Customer returned item",
        idempotency_key=f"ref1_{uuid.uuid4().hex[:8]}",
    )
    assert ref1.status == RefundStatus.SUCCEEDED
    assert p.total_refunded_paise == 40000

    # 2. Over-refund attempt: trying to refund 60001 paise when only 60000 paise remain
    with pytest.raises(SwitchException) as excinfo:
        refund_service.create_refund(
            db=db,
            merchant_user=merchant_user,
            payment_id=p.id,
            amount_paise=60001,
            reason="Exceeding limit",
            idempotency_key=f"ref_over_{uuid.uuid4().hex[:8]}",
        )
    assert excinfo.value.code == "EXCEEDS_REFUNDABLE_AMOUNT"

    # 3. Complete remaining refund of ₹600 (60000 paise)
    ref2 = refund_service.create_refund(
        db=db,
        merchant_user=merchant_user,
        payment_id=p.id,
        amount_paise=60000,
        reason="Remaining refund",
        idempotency_key=f"ref2_{uuid.uuid4().hex[:8]}",
    )
    assert ref2.status == RefundStatus.SUCCEEDED
    assert p.total_refunded_paise == 100000
