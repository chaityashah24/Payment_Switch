import uuid
import pytest
from app.models.payment import PaymentMethod
from app.services import payment_service
from app.core.exceptions import ConflictError


def test_idempotency_same_payload_returns_identical_payment(db, test_customer, test_merchant):
    idemp_key = f"idemp_{uuid.uuid4().hex[:12]}"
    amt = 150000

    # Call 1
    p1 = payment_service.initiate_payment(
        db=db,
        customer=test_customer,
        merchant_id=test_merchant.id,
        payment_method=PaymentMethod.UPI,
        amount_paise=amt,
        instrument_ref="customer@okaxis",
        idempotency_key=idemp_key,
        merchant_order_ref="ORDER-101",
    )

    # Call 2 with identical payload and key
    p2 = payment_service.initiate_payment(
        db=db,
        customer=test_customer,
        merchant_id=test_merchant.id,
        payment_method=PaymentMethod.UPI,
        amount_paise=amt,
        instrument_ref="customer@okaxis",
        idempotency_key=idemp_key,
        merchant_order_ref="ORDER-101",
    )

    assert p1.id == p2.id
    assert p1.bank_reference == p2.bank_reference


def test_idempotency_different_payload_raises_conflict(db, test_customer, test_merchant):
    idemp_key = f"idemp_{uuid.uuid4().hex[:12]}"

    p1 = payment_service.initiate_payment(
        db=db,
        customer=test_customer,
        merchant_id=test_merchant.id,
        payment_method=PaymentMethod.UPI,
        amount_paise=100000,
        instrument_ref="customer@okaxis",
        idempotency_key=idemp_key,
    )

    # Call with different amount using same idempotency key
    with pytest.raises(ConflictError):
        payment_service.initiate_payment(
            db=db,
            customer=test_customer,
            merchant_id=test_merchant.id,
            payment_method=PaymentMethod.UPI,
            amount_paise=200000,  # Differing payload!
            instrument_ref="customer@okaxis",
            idempotency_key=idemp_key,
        )
