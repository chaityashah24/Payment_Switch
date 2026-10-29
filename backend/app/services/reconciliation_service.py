import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models.reconciliation import (
    ReconciliationRun,
    ReconciliationException,
    RecRunStatus,
    RecExceptionType,
    RecExceptionSeverity,
    RecExceptionStatus,
)
from app.models.payment import Payment, PaymentStatus
from app.models.bank import BankTransaction
from app.models.ledger import JournalEntry, JournalLine
from app.models.user import User
from app.core.exceptions import NotFoundError, SwitchException
from app.services import audit_service


def run_three_way_reconciliation(
    db: Session,
    admin_user: User,
    period_start: datetime,
    period_end: datetime,
    bank_id: Optional[str] = None,
) -> ReconciliationRun:
    run_ref = f"REC-{int(period_start.timestamp())}-{int(period_end.timestamp())}"

    rec_run = ReconciliationRun(
        id=str(uuid.uuid4()),
        run_reference=run_ref,
        bank_id=bank_id,
        period_start=period_start,
        period_end=period_end,
        status=RecRunStatus.IN_PROGRESS,
    )
    db.add(rec_run)
    db.flush()

    # 1. Fetch switch payments in period
    query_payments = db.query(Payment).filter(
        Payment.created_at >= period_start,
        Payment.created_at <= period_end,
    )
    payments = query_payments.all()

    # 2. Fetch independent bank transactions in period
    query_bank_tx = db.query(BankTransaction).filter(
        BankTransaction.created_at >= period_start,
        BankTransaction.created_at <= period_end,
    )
    if bank_id:
        query_bank_tx = query_bank_tx.filter(BankTransaction.bank_id == bank_id)
    bank_transactions = query_bank_tx.all()

    bank_tx_by_ref = {tx.bank_reference: tx for tx in bank_transactions}
    bank_tx_by_payment_id = {tx.payment_id: tx for tx in bank_transactions if tx.payment_id}

    rec_run.total_switch_records = len(payments)
    rec_run.total_bank_records = len(bank_transactions)

    matched_count = 0
    exceptions = []

    # Check Switch Payments -> Bank Transactions & Ledger
    for p in payments:
        # Match against Bank Transaction
        b_tx = bank_tx_by_ref.get(p.bank_reference) or bank_tx_by_payment_id.get(p.id)

        if not b_tx:
            # Switch has payment, but bank has no record!
            if p.status == PaymentStatus.SUCCEEDED:
                exceptions.append(ReconciliationException(
                    id=str(uuid.uuid4()),
                    reconciliation_run_id=rec_run.id,
                    exception_type=RecExceptionType.MISSING_BANK_RECORD,
                    severity=RecExceptionSeverity.CRITICAL,
                    status=RecExceptionStatus.OPEN,
                    payment_id=p.id,
                    reference_key=p.bank_reference or p.id,
                    explanation=f"Payment {p.id} marked as SUCCEEDED in switch, but missing completely in simulated bank core records.",
                ))
            continue

        # Check Amount Mismatch
        if p.amount_paise != b_tx.amount_paise:
            exceptions.append(ReconciliationException(
                id=str(uuid.uuid4()),
                reconciliation_run_id=rec_run.id,
                exception_type=RecExceptionType.AMOUNT_MISMATCH,
                severity=RecExceptionSeverity.HIGH,
                status=RecExceptionStatus.OPEN,
                payment_id=p.id,
                bank_transaction_id=b_tx.id,
                reference_key=b_tx.bank_reference,
                explanation=f"Amount mismatch for Ref {b_tx.bank_reference}: Switch recorded ₹{p.amount_paise / 100:.2f}, while Bank recorded ₹{b_tx.amount_paise / 100:.2f}.",
            ))
            continue

        # Check Status Mismatch
        norm_switch_status = "SUCCESS" if p.status == PaymentStatus.SUCCEEDED else "DECLINED"
        norm_bank_status = "SUCCESS" if b_tx.status in ["SUCCESS", "CAPTURED"] else "DECLINED"

        if norm_switch_status != norm_bank_status:
            exceptions.append(ReconciliationException(
                id=str(uuid.uuid4()),
                reconciliation_run_id=rec_run.id,
                exception_type=RecExceptionType.STATUS_MISMATCH,
                severity=RecExceptionSeverity.HIGH,
                status=RecExceptionStatus.OPEN,
                payment_id=p.id,
                bank_transaction_id=b_tx.id,
                reference_key=b_tx.bank_reference,
                explanation=f"Status discrepancy for Ref {b_tx.bank_reference}: Switch status is '{p.status.value}', while Bank status is '{b_tx.status}'.",
            ))
            continue

        # Check 3-Way Match: Check Ledger Postings for SUCCEEDED payments
        if p.status == PaymentStatus.SUCCEEDED:
            journal_entry = (
                db.query(JournalEntry)
                .filter(
                    JournalEntry.source_type == "PAYMENT",
                    JournalEntry.source_id == p.id,
                )
                .first()
            )
            if not journal_entry:
                exceptions.append(ReconciliationException(
                    id=str(uuid.uuid4()),
                    reconciliation_run_id=rec_run.id,
                    exception_type=RecExceptionType.MISSING_LEDGER_POSTING,
                    severity=RecExceptionSeverity.CRITICAL,
                    status=RecExceptionStatus.OPEN,
                    payment_id=p.id,
                    reference_key=p.id,
                    explanation=f"Payment {p.id} is SUCCEEDED, but no corresponding double-entry journal entry exists in ledger.",
                ))
                continue

        matched_count += 1

    for exc in exceptions:
        db.add(exc)

    rec_run.total_matched = matched_count
    rec_run.total_exceptions = len(exceptions)
    rec_run.status = RecRunStatus.COMPLETED
    rec_run.completed_at = datetime.now(timezone.utc)

    audit_service.log_audit_event(
        db,
        action="RECONCILIATION_RUN_COMPLETED",
        entity_type="RECONCILIATION_RUN",
        entity_id=rec_run.id,
        user_id=admin_user.id,
        changes={
            "run_ref": run_ref,
            "matched": matched_count,
            "exceptions": len(exceptions),
        },
    )

    db.flush()
    return rec_run


def resolve_reconciliation_exception(
    db: Session,
    exception_id: str,
    admin_user: User,
    resolution_notes: str,
    mark_as: RecExceptionStatus = RecExceptionStatus.RESOLVED,
) -> ReconciliationException:
    exc = db.query(ReconciliationException).filter(ReconciliationException.id == exception_id).first()
    if not exc:
        raise NotFoundError("ReconciliationException", exception_id)

    exc.status = mark_as
    exc.resolution_notes = resolution_notes
    exc.resolved_by_user_id = admin_user.id
    exc.resolved_at = datetime.now(timezone.utc)

    audit_service.log_audit_event(
        db,
        action="RECONCILIATION_EXCEPTION_RESOLVED",
        entity_type="RECONCILIATION_EXCEPTION",
        entity_id=exc.id,
        user_id=admin_user.id,
        changes={"status": mark_as.value, "notes": resolution_notes},
    )

    db.flush()
    return exc
