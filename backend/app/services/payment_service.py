import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.payment import (
    Payment,
    PaymentAttempt,
    PaymentEvent,
    PaymentRoute,
    PaymentStatus,
    PaymentMethod,
    IdempotencyRecord,
)
from app.models.user import User
from app.models.merchant import Merchant, MerchantStatus
from app.models.account import (
    SimulatedAccount,
    PaymentInstrument,
    BalanceHold,
    HoldStatus,
    SimulatedBank,
)
from app.models.scenario import SimulationScenario
from app.models.risk import RiskAction
from app.models.job import BackgroundJob, JobType, JobStatus
from app.core.exceptions import (
    NotFoundError,
    ConflictError,
    PermissionDeniedError,
    SwitchException,
    InsufficientFundsError,
)
from app.core.state_machine import validate_payment_transition
from app.core.correlation import get_correlation_id
from app.services import ledger_service, risk_service, bank_service, audit_service


def compute_request_hash(data: Dict[str, Any]) -> str:
    canonical = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def get_active_simulation_scenario(db: Session, route_id: Optional[str] = None) -> Optional[str]:
    scenario = db.query(SimulationScenario).filter(SimulationScenario.is_active == True).first()
    if not scenario:
        return None
    if scenario.apply_to_next_only:
        scenario.is_active = False
        db.flush()
    return scenario.name


def add_payment_event(
    db: Session,
    payment: Payment,
    event_type: str,
    from_status: Optional[str],
    to_status: str,
    details: Optional[str] = None,
) -> PaymentEvent:
    event = PaymentEvent(
        id=str(uuid.uuid4()),
        payment_id=payment.id,
        event_type=event_type,
        from_status=from_status,
        to_status=to_status,
        correlation_id=get_correlation_id(),
        details=details,
    )
    db.add(event)
    db.flush()
    return event


def initiate_payment(
    db: Session,
    customer: User,
    merchant_id: str,
    payment_method: PaymentMethod,
    amount_paise: int,
    instrument_ref: str,
    idempotency_key: str,
    merchant_order_ref: Optional[str] = None,
    demo_auth_token: Optional[str] = None,
) -> Payment:
    # Step 1: Idempotency enforcement
    req_payload = {
        "customer_id": customer.id,
        "merchant_id": merchant_id,
        "method": payment_method.value,
        "amount_paise": amount_paise,
        "instrument_ref": instrument_ref,
        "order_ref": merchant_order_ref,
    }
    req_hash = compute_request_hash(req_payload)

    existing_idemp = (
        db.query(IdempotencyRecord)
        .filter(
            IdempotencyRecord.actor_id == customer.id,
            IdempotencyRecord.operation == "PAYMENT_INITIATE",
            IdempotencyRecord.idempotency_key == idempotency_key,
        )
        .first()
    )

    if existing_idemp:
        if existing_idemp.request_hash == req_hash and existing_idemp.payment_id:
            # Return identical original payment
            existing_payment = db.query(Payment).filter(Payment.id == existing_idemp.payment_id).first()
            if existing_payment:
                return existing_payment
        else:
            raise ConflictError(
                f"Idempotency key '{idempotency_key}' already used with a different request payload."
            )

    # Step 2: Validate merchant
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        raise NotFoundError("Merchant", merchant_id)

    # Step 3: Snapshot fees
    bps = merchant.fee_percentage_bps
    flat_paise = merchant.fee_flat_paise
    calculated_fee = int(round((amount_paise * bps) / 10000.0)) + flat_paise

    # Step 4: Create durable payment record in CREATED state
    payment = Payment(
        id=str(uuid.uuid4()),
        customer_id=customer.id,
        merchant_id=merchant.id,
        payment_method=payment_method,
        amount_paise=amount_paise,
        currency="INR",
        fee_bps_snapshot=bps,
        fee_flat_paise_snapshot=flat_paise,
        calculated_fee_paise=calculated_fee,
        status=PaymentStatus.CREATED,
        merchant_order_ref=merchant_order_ref,
        idempotency_key=idempotency_key,
        instrument_ref=instrument_ref,
        total_refunded_paise=0,
    )
    db.add(payment)
    db.flush()

    # Save idempotency record
    idemp_rec = IdempotencyRecord(
        id=str(uuid.uuid4()),
        actor_id=customer.id,
        operation="PAYMENT_INITIATE",
        idempotency_key=idempotency_key,
        request_hash=req_hash,
        payment_id=payment.id,
    )
    db.add(idemp_rec)
    db.flush()

    add_payment_event(
        db,
        payment,
        event_type="PAYMENT_CREATED",
        from_status=None,
        to_status=PaymentStatus.CREATED.value,
        details=f"Payment record created for ₹{amount_paise / 100:.2f} to {merchant.business_name}",
    )

    # Step 5: Check active simulation scenario
    scenario = get_active_simulation_scenario(db)
    payment.active_scenario = scenario

    # Step 6: Risk rule evaluation
    risk_action, risk_reason, matched_rule_id = risk_service.evaluate_risk(
        db, customer.id, merchant, amount_paise, payment
    )
    risk_service.record_risk_decision(
        db, payment.id, risk_action, risk_reason, matched_rule_id
    )

    if risk_action == RiskAction.DECLINE:
        validate_payment_transition(payment.status, PaymentStatus.DECLINED)
        payment.status = PaymentStatus.DECLINED
        payment.error_code = "RISK_DECLINE"
        payment.error_message = risk_reason
        add_payment_event(
            db,
            payment,
            event_type="RISK_DECLINED",
            from_status=PaymentStatus.CREATED.value,
            to_status=PaymentStatus.DECLINED.value,
            details=risk_reason,
        )
        db.flush()
        return payment

    if risk_action == RiskAction.REVIEW:
        validate_payment_transition(payment.status, PaymentStatus.PENDING)
        payment.status = PaymentStatus.PENDING
        payment.error_code = "RISK_REVIEW_REQUIRED"
        payment.error_message = f"Transaction held for compliance & fraud review: {risk_reason}"
        add_payment_event(
            db,
            payment,
            event_type="RISK_FLAGGED_FOR_REVIEW",
            from_status=PaymentStatus.CREATED.value,
            to_status=PaymentStatus.PENDING.value,
            details=risk_reason,
        )
        db.flush()
        return payment

    # Step 7: Select active route
    route = (
        db.query(PaymentRoute)
        .filter(PaymentRoute.payment_method == payment_method, PaymentRoute.is_enabled == True)
        .order_by(PaymentRoute.priority.asc())
        .first()
    )
    bank_id = route.bank_id if route else "SIM_BANK_DEFAULT"

    # Step 8: Find customer account and check available balance
    customer_account = (
        db.query(SimulatedAccount)
        .filter(SimulatedAccount.user_id == customer.id)
        .first()
    )

    # If no simulated account exists or balance is too low
    if scenario == "INSUFFICIENT_FUNDS" or (customer_account and customer_account.available_balance_paise < amount_paise):
        validate_payment_transition(payment.status, PaymentStatus.DECLINED)
        payment.status = PaymentStatus.DECLINED
        payment.error_code = "INSUFFICIENT_FUNDS"
        payment.error_message = "Customer account balance is insufficient for payment amount"
        add_payment_event(
            db,
            payment,
            event_type="DECLINED_INSUFFICIENT_FUNDS",
            from_status=PaymentStatus.CREATED.value,
            to_status=PaymentStatus.DECLINED.value,
            details=payment.error_message,
        )
        db.flush()
        return payment

    # Create balance hold on customer account
    hold = None
    if customer_account:
        customer_account.available_balance_paise -= amount_paise
        hold = BalanceHold(
            id=str(uuid.uuid4()),
            payment_id=payment.id,
            customer_account_id=customer_account.id,
            amount_paise=amount_paise,
            status=HoldStatus.ACTIVE,
        )
        db.add(hold)
        db.flush()

    # Step 9: Transition to PROCESSING (or QUEUED for NEFT)
    if payment_method == PaymentMethod.NEFT:
        validate_payment_transition(payment.status, PaymentStatus.QUEUED)
        payment.status = PaymentStatus.QUEUED
        add_payment_event(
            db,
            payment,
            event_type="PAYMENT_QUEUED_NEFT",
            from_status=PaymentStatus.CREATED.value,
            to_status=PaymentStatus.QUEUED.value,
            details="Queued for next simulated NEFT clearing batch",
        )
    else:
        validate_payment_transition(payment.status, PaymentStatus.PROCESSING)
        payment.status = PaymentStatus.PROCESSING
        add_payment_event(
            db,
            payment,
            event_type="PAYMENT_PROCESSING",
            from_status=PaymentStatus.CREATED.value,
            to_status=PaymentStatus.PROCESSING.value,
            details=f"Routing payment via bank route {bank_id}",
        )

    # Create Payment Attempt
    attempt = PaymentAttempt(
        id=str(uuid.uuid4()),
        payment_id=payment.id,
        attempt_number=1,
        route_id=route.id if route else None,
        bank_id=bank_id,
        status="PENDING",
        request_payload=json.dumps({"method": payment_method.value, "amount": amount_paise}),
    )
    db.add(attempt)
    db.flush()

    # Step 10: Call bank adapter / simulated bank
    bank_result, bank_tx = bank_service.execute_bank_transaction(
        db, payment, scenario=scenario
    )

    attempt.bank_reference = bank_result.bank_reference
    attempt.status = bank_result.status
    attempt.latency_ms = bank_result.latency_ms
    attempt.response_payload = json.dumps(bank_result.raw_response)
    attempt.completed_at = datetime.now(timezone.utc)
    payment.bank_reference = bank_result.bank_reference

    # Step 11: Handle bank outcome
    if payment_method == PaymentMethod.NEFT:
        # Enqueue background job to settle batch
        job = BackgroundJob(
            id=str(uuid.uuid4()),
            job_type=JobType.NEFT_BATCH_PROCESS,
            payload=json.dumps({"payment_id": payment.id}),
            status=JobStatus.QUEUED,
        )
        db.add(job)
        db.flush()
        return payment

    if scenario == "TIMEOUT_AFTER_BANK_SUCCESS":
        # Crucial scenario: bank succeeded, but switch experienced a timeout!
        # Status remains PENDING. Hold remains active. NO double debit!
        validate_payment_transition(payment.status, PaymentStatus.PENDING)
        payment.status = PaymentStatus.PENDING
        payment.error_code = "BANK_TIMEOUT_UNKNOWN_OUTCOME"
        payment.error_message = "Gateway timed out waiting for bank acknowledgement. Payment is PENDING resolution."
        add_payment_event(
            db,
            payment,
            event_type="TIMEOUT_AFTER_BANK_SUCCESS_OBSERVED",
            from_status=PaymentStatus.PROCESSING.value,
            to_status=PaymentStatus.PENDING.value,
            details="Network acknowledgment lost. Bank status verified independently during reconciliation.",
        )
        # Enqueue delayed resolution job
        job = BackgroundJob(
            id=str(uuid.uuid4()),
            job_type=JobType.PROCESS_DELAYED_PAYMENT,
            payload=json.dumps({"payment_id": payment.id}),
            status=JobStatus.QUEUED,
        )
        db.add(job)
        db.flush()
        return payment

    if bank_result.status == "SUCCESS":
        validate_payment_transition(payment.status, PaymentStatus.SUCCEEDED)
        payment.status = PaymentStatus.SUCCEEDED
        payment.error_code = None
        payment.error_message = None

        # Capture hold and debit actual customer balance
        if hold and customer_account:
            hold.status = HoldStatus.CAPTURED
            hold.resolved_at = datetime.now(timezone.utc)
            customer_account.balance_paise -= amount_paise

        # Post balanced double-entry ledger entry
        ledger_service.post_payment_capture(db, payment)

        add_payment_event(
            db,
            payment,
            event_type="PAYMENT_SUCCEEDED",
            from_status=PaymentStatus.PROCESSING.value,
            to_status=PaymentStatus.SUCCEEDED.value,
            details=f"Payment succeeded at bank (Ref: {bank_result.bank_reference}). Double-entry ledger posted.",
        )

    elif bank_result.status == "DECLINED":
        validate_payment_transition(payment.status, PaymentStatus.DECLINED)
        payment.status = PaymentStatus.DECLINED
        payment.error_code = bank_result.error_code or "BANK_DECLINED"
        payment.error_message = bank_result.error_message or "Bank declined authorization"

        # Release hold
        if hold and customer_account:
            hold.status = HoldStatus.RELEASED
            hold.resolved_at = datetime.now(timezone.utc)
            customer_account.available_balance_paise += amount_paise

        add_payment_event(
            db,
            payment,
            event_type="PAYMENT_DECLINED",
            from_status=PaymentStatus.PROCESSING.value,
            to_status=PaymentStatus.DECLINED.value,
            details=payment.error_message,
        )

    else:  # FAILED
        validate_payment_transition(payment.status, PaymentStatus.FAILED)
        payment.status = PaymentStatus.FAILED
        payment.error_code = bank_result.error_code or "BANK_FAILED"
        payment.error_message = bank_result.error_message or "Bank connection failed"

        # Release hold
        if hold and customer_account:
            hold.status = HoldStatus.RELEASED
            hold.resolved_at = datetime.now(timezone.utc)
            customer_account.available_balance_paise += amount_paise

        add_payment_event(
            db,
            payment,
            event_type="PAYMENT_FAILED",
            from_status=PaymentStatus.PROCESSING.value,
            to_status=PaymentStatus.FAILED.value,
            details=payment.error_message,
        )

    audit_service.log_audit_event(
        db,
        action="PAYMENT_INITIATED",
        entity_type="PAYMENT",
        entity_id=payment.id,
        user_id=customer.id,
        changes={"amount_paise": amount_paise, "status": payment.status.value},
    )

    db.flush()
    return payment


def resolve_pending_payment(db: Session, payment_id: str) -> Payment:
    """Safely queries bank and resolves a PENDING payment exactly once."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment or payment.status != PaymentStatus.PENDING:
        return payment

    # Check bank transaction status
    bank_tx = (
        db.query(bank_service.BankTransaction)
        .filter(bank_service.BankTransaction.payment_id == payment.id)
        .first()
    )

    customer_account = (
        db.query(SimulatedAccount)
        .filter(SimulatedAccount.user_id == payment.customer_id)
        .first()
    )
    hold = (
        db.query(BalanceHold)
        .filter(BalanceHold.payment_id == payment.id, BalanceHold.status == HoldStatus.ACTIVE)
        .first()
    )

    if bank_tx and bank_tx.status == "SUCCESS":
        validate_payment_transition(payment.status, PaymentStatus.SUCCEEDED)
        payment.status = PaymentStatus.SUCCEEDED
        payment.error_code = None
        payment.error_message = None

        if hold and customer_account:
            hold.status = HoldStatus.CAPTURED
            hold.resolved_at = datetime.now(timezone.utc)
            customer_account.balance_paise -= payment.amount_paise

        # Post ledger
        ledger_service.post_payment_capture(db, payment)

        add_payment_event(
            db,
            payment,
            event_type="PENDING_RESOLVED_SUCCEEDED",
            from_status=PaymentStatus.PENDING.value,
            to_status=PaymentStatus.SUCCEEDED.value,
            details=f"Authoritative bank confirmation received for Ref {bank_tx.bank_reference}. Funds captured.",
        )
    else:
        validate_payment_transition(payment.status, PaymentStatus.FAILED)
        payment.status = PaymentStatus.FAILED

        if hold and customer_account:
            hold.status = HoldStatus.RELEASED
            hold.resolved_at = datetime.now(timezone.utc)
            customer_account.available_balance_paise += payment.amount_paise

        add_payment_event(
            db,
            payment,
            event_type="PENDING_RESOLVED_FAILED",
            from_status=PaymentStatus.PENDING.value,
            to_status=PaymentStatus.FAILED.value,
            details="No affirmative authorization found at bank. Hold released.",
        )

    db.flush()
    return payment
