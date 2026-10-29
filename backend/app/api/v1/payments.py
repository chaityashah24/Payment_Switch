from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app.models.user import User, UserRole
from app.schemas.payment import (
    PaymentInitiateRequest,
    PaymentResponse,
    PaymentEventResponse,
    ReceiptResponse,
)
from app.services import payment_service
from app.api.deps import get_current_user, require_customer
from app.core.exceptions import NotFoundError, PermissionDeniedError

router = APIRouter(prefix="/payments", tags=["Payments"])


def _check_payment_access(payment: Payment, user: User):
    if user.role == UserRole.ADMIN:
        return
    if user.role == UserRole.CUSTOMER and payment.customer_id == user.id:
        return
    if user.role == UserRole.MERCHANT:
        user_merchants = {m.merchant_id for m in user.merchant_memberships}
        if payment.merchant_id in user_merchants:
            return
    raise PermissionDeniedError("You do not have access to view this payment.")


def _to_payment_response(p: Payment) -> PaymentResponse:
    events = [
        PaymentEventResponse(
            id=e.id,
            event_type=e.event_type,
            from_status=e.from_status,
            to_status=e.to_status,
            correlation_id=e.correlation_id,
            details=e.details,
            created_at=e.created_at,
        )
        for e in p.events
    ] if p.events else []

    return PaymentResponse(
        id=p.id,
        customer_id=p.customer_id,
        merchant_id=p.merchant_id,
        merchant_name=p.merchant.business_name if p.merchant else None,
        payment_method=p.payment_method,
        amount_paise=p.amount_paise,
        currency=p.currency,
        status=p.status,
        fee_bps_snapshot=p.fee_bps_snapshot,
        fee_flat_paise_snapshot=p.fee_flat_paise_snapshot,
        calculated_fee_paise=p.calculated_fee_paise,
        net_merchant_paise=p.amount_paise - p.calculated_fee_paise,
        merchant_order_ref=p.merchant_order_ref,
        idempotency_key=p.idempotency_key,
        instrument_ref=p.instrument_ref,
        bank_reference=p.bank_reference,
        active_scenario=p.active_scenario,
        error_code=p.error_code,
        error_message=p.error_message,
        settled_item_id=p.settled_item_id,
        total_refunded_paise=p.total_refunded_paise,
        created_at=p.created_at,
        updated_at=p.updated_at,
        events=events,
    )


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def initiate_payment(
    data: PaymentInitiateRequest,
    customer: User = Depends(require_customer),
    db: Session = Depends(get_db),
):
    payment = payment_service.initiate_payment(
        db=db,
        customer=customer,
        merchant_id=data.merchant_id,
        payment_method=data.payment_method,
        amount_paise=data.amount_paise,
        instrument_ref=data.instrument_ref,
        idempotency_key=data.idempotency_key,
        merchant_order_ref=data.merchant_order_ref,
        demo_auth_token=data.demo_auth_token,
    )
    db.commit()
    db.refresh(payment)
    return _to_payment_response(payment)


@router.get("", response_model=List[PaymentResponse])
def list_payments(
    status_filter: Optional[PaymentStatus] = None,
    method_filter: Optional[PaymentMethod] = None,
    merchant_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Payment)

    # Role enforcement
    if current_user.role == UserRole.CUSTOMER:
        query = query.filter(Payment.customer_id == current_user.id)
    elif current_user.role == UserRole.MERCHANT:
        merchant_ids = [m.merchant_id for m in current_user.merchant_memberships]
        query = query.filter(Payment.merchant_id.in_(merchant_ids))
    elif merchant_id:
        query = query.filter(Payment.merchant_id == merchant_id)

    if status_filter:
        query = query.filter(Payment.status == status_filter)
    if method_filter:
        query = query.filter(Payment.payment_method == method_filter)

    payments = query.order_by(desc(Payment.created_at)).offset(offset).limit(limit).all()
    return [_to_payment_response(p) for p in payments]


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment_details(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise NotFoundError("Payment", payment_id)

    _check_payment_access(payment, current_user)
    return _to_payment_response(payment)


@router.get("/{payment_id}/timeline", response_model=List[PaymentEventResponse])
def get_payment_timeline(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise NotFoundError("Payment", payment_id)

    _check_payment_access(payment, current_user)
    return [
        PaymentEventResponse(
            id=e.id,
            event_type=e.event_type,
            from_status=e.from_status,
            to_status=e.to_status,
            correlation_id=e.correlation_id,
            details=e.details,
            created_at=e.created_at,
        )
        for e in payment.events
    ]


@router.get("/{payment_id}/receipt", response_model=ReceiptResponse)
def get_payment_receipt(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise NotFoundError("Payment", payment_id)

    _check_payment_access(payment, current_user)

    merchant_name = payment.merchant.business_name if payment.merchant else "Merchant"
    customer_name = payment.customer.full_name if payment.customer else "Customer"

    return ReceiptResponse(
        payment_id=payment.id,
        receipt_number=f"RCP-{payment.id[:8].upper()}",
        merchant_name=merchant_name,
        customer_name=customer_name,
        amount_paise=payment.amount_paise,
        amount_inr=f"₹{payment.amount_paise / 100:.2f}",
        currency=payment.currency,
        payment_method=payment.payment_method.value,
        status=payment.status.value,
        bank_reference=payment.bank_reference,
        timestamp=payment.created_at,
    )


@router.post("/{payment_id}/resolve", response_model=PaymentResponse)
def resolve_pending_payment_status(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise NotFoundError("Payment", payment_id)

    _check_payment_access(payment, current_user)
    resolved = payment_service.resolve_pending_payment(db, payment_id)
    db.commit()
    db.refresh(resolved)
    return _to_payment_response(resolved)
