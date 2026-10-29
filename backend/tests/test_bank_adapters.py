import uuid
from app.models.payment import PaymentMethod, Payment
from app.bank_adapters import get_bank_adapter
from app.bank_adapters.upi_adapter import UPIBankAdapter
from app.bank_adapters.card_adapter import CardBankAdapter
from app.bank_adapters.neft_adapter import NEFTBankAdapter
from app.bank_adapters.rtgs_adapter import RTGSBankAdapter


def test_upi_adapter():
    adapter = get_bank_adapter(PaymentMethod.UPI)
    assert isinstance(adapter, UPIBankAdapter)
    assert adapter.validate_vpa("user@okbank") is True
    assert adapter.validate_vpa("invalidvpa") is False

    dummy_payment = Payment(
        id=str(uuid.uuid4()),
        amount_paise=10000,
        instrument_ref="user@okbank",
        currency="INR",
    )
    res = adapter.process_payment(dummy_payment)
    assert res.is_success is True
    assert res.status == "SUCCESS"
    assert res.bank_reference.startswith("UPI")


def test_card_adapter_auth_and_capture():
    adapter = get_bank_adapter(PaymentMethod.CARD)
    assert isinstance(adapter, CardBankAdapter)

    dummy_payment = Payment(
        id=str(uuid.uuid4()),
        amount_paise=250000,
        instrument_ref="tok_card_1234",
        currency="INR",
    )
    auth_res = adapter.authorize(dummy_payment)
    assert auth_res.is_success is True
    assert auth_res.bank_reference.startswith("AUTH")

    cap_res = adapter.capture(dummy_payment)
    assert cap_res.is_success is True
    assert cap_res.bank_reference.startswith("CAP")


def test_neft_adapter_batch_queuing():
    adapter = get_bank_adapter(PaymentMethod.NEFT)
    assert isinstance(adapter, NEFTBankAdapter)

    dummy_payment = Payment(
        id=str(uuid.uuid4()),
        amount_paise=50000,
        instrument_ref="A/C 12345678",
        currency="INR",
    )
    res = adapter.process_payment(dummy_payment)
    assert res.status == "QUEUED"
    assert "NEFT-BATCH" in res.bank_reference


def test_rtgs_adapter_threshold():
    adapter = get_bank_adapter(PaymentMethod.RTGS)
    assert isinstance(adapter, RTGSBankAdapter)

    # Sub-threshold payment (< ₹2,000 / 200000 paise)
    small_payment = Payment(
        id=str(uuid.uuid4()),
        amount_paise=50000,
        instrument_ref="A/C 12345678",
        currency="INR",
    )
    res_declined = adapter.process_payment(small_payment)
    assert res_declined.status == "DECLINED"
    assert res_declined.error_code == "RTGS_MIN_AMOUNT_NOT_MET"

    # Eligible gross payment (>= ₹2,000 / 200000 paise)
    large_payment = Payment(
        id=str(uuid.uuid4()),
        amount_paise=250000,
        instrument_ref="A/C 12345678",
        currency="INR",
    )
    res_success = adapter.process_payment(large_payment)
    assert res_success.status == "SUCCESS"
    assert res_success.bank_reference.startswith("RTGS")
