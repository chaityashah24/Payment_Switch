import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.models.refund import Refund, RefundStatus
from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from app.models.account import SimulatedAccount
from app.core.exceptions import (
    NotFoundError,
    ConflictError,
    PermissionDeniedError,
    SwitchException,
)
from app.core.state_machine import validate_refund_transition
from app.services import ledger_service, audit_service, payment_service


def create_refund(
    db: Session,
    merchant_user: User,
    payment_id: str,
    amount_paise: int,
    reason: str,
    idempotency_key: str,
) -> Refund:
    # Check idempotency
    existing_refund = db.query(Refund).filter(Refund.idempotency_key == idempotency_key).first()
    if existing_refund:
        if existing_refund.payment_id == payment_id and existing_refund.amount_paise == amount_paise:
            return existing_refund
        raise ConflictError(f"Refund idempotency key '{idempotency_key}' already exists with different payload.")

    # Find payment
    payment = db.query(Payment).filter(Payment.id == payment_id).with_for_update().first()
    if not payment:
        raise NotFoundError("Payment", payment_id)

    # Verify merchant ownership (unless ADMIN)
    if merchant_user.role.value != "ADMIN":
        membership = [m for m in merchant_user.merchant_memberships if m.merchant_id == payment.merchant_id]
        if not membership:
            raise PermissionDeniedError("You can only issue refunds for your own merchant payments.")

    # Invariant: Payment must be SUCCEEDED
    if payment.status != PaymentStatus.SUCCEEDED:
        raise SwitchException(
            code="PAYMENT_NOT_REFUNDABLE",
            message=f"Only SUCCEEDED payments can be refunded. Current status is {payment.status.value}",
        )

    # Invariant: Total refunded cannot exceed original captured amount
    available_refundable = payment.amount_paise - payment.total_refunded_paise
    if amount_paise > available_refundable:
        raise SwitchException(
            code="EXCEEDS_REFUNDABLE_AMOUNT",
            message=f"Requested refund ₹{amount_paise / 100:.2f} exceeds available refundable balance ₹{available_refundable / 100:.2f}",
        )

    # Calculate proportional fee refund
    fee_refund = 0
    if payment.calculated_fee_paise > 0 and payment.amount_paise > 0:
        fee_refund = int(round((payment.calculated_fee_paise * amount_paise) / payment.amount_paise))

    # Create refund record in PENDING
    refund = Refund(
        id=str(uuid.uuid4()),
        payment_id=payment.id,
        merchant_id=payment.merchant_id,
        amount_paise=amount_paise,
        fee_refund_paise=fee_refund,
        currency=payment.currency,
        reason=reason,
        idempotency_key=idempotency_key,
        status=RefundStatus.PENDING,
        bank_reference=f"REF-{uuid.uuid4().hex[:8].upper()}",
    )
    db.add(refund)
    db.flush()

    # Transition to SUCCEEDED and apply ledger updates
    validate_refund_transition(refund.status, RefundStatus.SUCCEEDED)
    refund.status = RefundStatus.SUCCEEDED
    refund.completed_at = datetime.now(timezone.utc)

    # Update payment refunded total
    payment.total_refunded_paise += amount_paise

    # Credit customer simulated bank account
    customer_account = (
        db.query(SimulatedAccount)
        .filter(SimulatedAccount.user_id == payment.customer_id)
        .first()
    )
    if customer_account:
        customer_account.balance_paise += amount_paise
        customer_account.available_balance_paise += amount_paise

    # Double-entry ledger reversal posting
    ledger_service.post_refund(db, refund, payment)

    # Add payment timeline event
    payment_service.add_payment_event(
        db,
        payment,
        event_type="REFUND_PROCESSED",
        from_status=payment.status.value,
        to_status=payment.status.value,
        details=f"Refund of ₹{amount_paise / 100:.2f} processed. Reason: {reason}",
    )

    audit_service.log_audit_event(
        db,
        action="REFUND_CREATED",
        entity_type="REFUND",
        entity_id=refund.id,
        user_id=merchant_user.id,
        changes={"amount_paise": amount_paise, "payment_id": payment_id},
    )

    db.flush()
    return refund
