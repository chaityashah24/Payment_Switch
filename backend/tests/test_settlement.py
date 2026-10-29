import uuid
import pytest
from app.models.payment import PaymentMethod
from app.models.settlement import BatchStatus
from app.services import payment_service, settlement_service
from app.core.exceptions import SwitchException


def test_settlement_batch_execution_and_deduplication(db, test_admin, test_customer, test_merchant):
    # 1. Create payment
    p = payment_service.initiate_payment(
        db=db,
        customer=test_customer,
        merchant_id=test_merchant.id,
        payment_method=PaymentMethod.UPI,
        amount_paise=100000,
        instrument_ref="customer@okaxis",
        idempotency_key=f"settle_pay_{uuid.uuid4().hex[:8]}",
    )

    # 2. Preview
    preview = settlement_service.calculate_settlement_preview(db)
    assert preview["total_gross_paise"] >= 100000

    # 3. Create & execute batch
    batch = settlement_service.create_and_execute_settlement_batch(db, test_admin)
    assert batch.status == BatchStatus.COMPLETED
    assert len(batch.items) >= 1

    # 4. Immediate second run should find no unallocated transactions
    with pytest.raises(SwitchException) as excinfo:
        settlement_service.create_and_execute_settlement_batch(db, test_admin)
    assert excinfo.value.code == "NO_ELIGIBLE_TRANSACTIONS"
