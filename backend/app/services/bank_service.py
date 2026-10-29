import uuid
import json
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.models.payment import Payment
from app.models.bank import BankTransaction, BankEvent
from app.bank_adapters import get_bank_adapter
from app.bank_adapters.base import BankExecutionResult


def execute_bank_transaction(
    db: Session,
    payment: Payment,
    scenario: Optional[str] = None,
) -> Tuple[BankExecutionResult, Optional[BankTransaction]]:
    adapter = get_bank_adapter(payment.payment_method)
    result = adapter.process_payment(payment, scenario=scenario)

    # Independent bank-side persistence
    bank_tx = None
    if scenario != "RECONCILIATION_MISSING_RECORD":
        # Amount recorded by bank:
        bank_amount = payment.amount_paise
        if scenario == "RECONCILIATION_AMOUNT_MISMATCH":
            # Bank recorded ₹50 less due to simulated discrepancy
            bank_amount = max(0, payment.amount_paise - 5000)

        # Status recorded by bank:
        bank_status = result.status
        if scenario == "RECONCILIATION_STATUS_MISMATCH":
            bank_status = "SUCCESS"

        bank_tx = BankTransaction(
            id=str(uuid.uuid4()),
            bank_id=payment.attempts[0].bank_id if payment.attempts else "SIM_DEFAULT",
            payment_id=payment.id,
            bank_reference=result.bank_reference,
            amount_paise=bank_amount,
            currency=payment.currency,
            transaction_type="DEBIT",
            status=bank_status,
            scenario_applied=scenario,
            raw_payload=json.dumps(result.raw_response),
        )
        db.add(bank_tx)
        db.flush()

        # Add bank event
        bank_event = BankEvent(
            id=str(uuid.uuid4()),
            bank_transaction_id=bank_tx.id,
            event_type="BANK_PROCESSED",
            event_data=json.dumps({"result": result.status, "latency_ms": result.latency_ms}),
        )
        db.add(bank_event)
        db.flush()

    return result, bank_tx
