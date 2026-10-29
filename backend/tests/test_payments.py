import uuid
import pytest
from app.models.payment import PaymentStatus, PaymentMethod
from app.models.account import HoldStatus
from app.services import payment_service, ledger_service


def test_payment_initiation_success_and_ledger_balance(db, test_customer, test_merchant):
    idemp_key = f"idemp_{uuid.uuid4().hex[:10]}"
    amt = 250000  # ₹2,500.00

    payment = payment_service.initiate_payment(
        db=db,
        customer=test_customer,
        merchant_id=test_merchant.id,
        payment_method=PaymentMethod.UPI,
        amount_paise=amt,
        instrument_ref="customer@okaxis",
        idempotency_key=idemp_key,
        merchant_order_ref="ORD-TEST-001",
        demo_auth_token="PIN_1234",
    )

    assert payment.status == PaymentStatus.SUCCEEDED
    assert payment.amount_paise == amt
    # Fee: 150 bps (1.5%) of 250000 = 3750 + 100 flat = 3850
    assert payment.calculated_fee_paise == 3850
    assert payment.bank_reference is not None

    # Check customer account balance debited
    acc = test_customer.simulated_accounts[0]
    db.refresh(acc)
    assert acc.balance_paise == 1000000 - amt

    # Check ledger invariants
    integrity = ledger_service.verify_ledger_invariants(db)
    assert integrity["is_balanced"] is True


def test_payment_insufficient_funds_no_debit(db, test_customer, test_merchant):
    idemp_key = f"idemp_{uuid.uuid4().hex[:10]}"
    huge_amount = 50000000  # ₹5,00,000 (exceeds balance of ₹10,000)

    payment = payment_service.initiate_payment(
        db=db,
        customer=test_customer,
        merchant_id=test_merchant.id,
        payment_method=PaymentMethod.UPI,
        amount_paise=huge_amount,
        instrument_ref="customer@okaxis",
        idempotency_key=idemp_key,
    )

    assert payment.status == PaymentStatus.DECLINED
    assert payment.error_code == "INSUFFICIENT_FUNDS"

    # Customer account balance must NOT be altered
    acc = test_customer.simulated_accounts[0]
    db.refresh(acc)
    assert acc.balance_paise == 1000000
    assert acc.available_balance_paise == 1000000


def test_timeout_after_bank_success_and_resolution(db, test_customer, test_merchant):
    from app.models.scenario import SimulationScenario
    scenario = db.query(SimulationScenario).filter(SimulationScenario.name == "TIMEOUT_AFTER_BANK_SUCCESS").first()
    if not scenario:
        scenario = SimulationScenario(
            id=str(uuid.uuid4()),
            name="TIMEOUT_AFTER_BANK_SUCCESS",
            description="Timeout after bank success test",
            is_active=True,
        )
        db.add(scenario)
    else:
        scenario.is_active = True
    db.flush()

    idemp_key = f"idemp_{uuid.uuid4().hex[:10]}"
    amt = 100000

    # Payment initiated: bank processed, but acknowledgement was lost in transit
    payment = payment_service.initiate_payment(
        db=db,
        customer=test_customer,
        merchant_id=test_merchant.id,
        payment_method=PaymentMethod.UPI,
        amount_paise=amt,
        instrument_ref="customer@okaxis",
        idempotency_key=idemp_key,
    )

    # Must be PENDING, NOT FAILED!
    assert payment.status == PaymentStatus.PENDING
    assert payment.error_code == "BANK_TIMEOUT_UNKNOWN_OUTCOME"

    # Hold is still active
    hold = payment.holds[0]
    assert hold.status == HoldStatus.ACTIVE

    # Safe resolution later (via job or manual refresh)
    resolved_payment = payment_service.resolve_pending_payment(db, payment.id)
    assert resolved_payment.status == PaymentStatus.SUCCEEDED
    assert hold.status == HoldStatus.CAPTURED

    # Deactivate scenario
    db.query(SimulationScenario).filter(SimulationScenario.name == "TIMEOUT_AFTER_BANK_SUCCESS").update({"is_active": False})
    db.flush()
