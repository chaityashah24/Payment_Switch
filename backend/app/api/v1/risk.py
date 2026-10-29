from typing import List
from datetime import datetime, timezone
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models.risk import RiskRule, RiskDecision, RiskAction
from app.models.payment import Payment, PaymentStatus
from app.models.user import User
from app.models.account import SimulatedAccount, BalanceHold, HoldStatus
from app.schemas.risk import (
    RiskRuleCreate,
    RiskRuleResponse,
    RiskDecisionResponse,
    RiskReviewResolveRequest,
)
from app.schemas.payment import PaymentResponse
from app.services import payment_service, ledger_service, audit_service
from app.api.deps import require_admin
from app.core.exceptions import NotFoundError, SwitchException

router = APIRouter(prefix="/risk", tags=["Risk Rules & Compliance"])


@router.get("/rules", response_model=List[RiskRuleResponse])
def list_risk_rules(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return db.query(RiskRule).order_by(desc(RiskRule.created_at)).all()


@router.post("/rules", response_model=RiskRuleResponse, status_code=status.HTTP_201_CREATED)
def create_risk_rule(
    data: RiskRuleCreate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    rule = RiskRule(
        id=str(uuid.uuid4()),
        name=data.name,
        description=data.description,
        rule_type=data.rule_type,
        threshold_value=data.threshold_value,
        window_seconds=data.window_seconds,
        action=data.action,
        is_active=data.is_active,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.get("/decisions", response_model=List[RiskDecisionResponse])
def list_risk_decisions(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return db.query(RiskDecision).order_by(desc(RiskDecision.created_at)).limit(100).all()


@router.get("/review-queue", response_model=List[RiskDecisionResponse])
def get_review_queue(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return (
        db.query(RiskDecision)
        .filter(RiskDecision.action == RiskAction.REVIEW, RiskDecision.resolution_action == None)
        .order_by(desc(RiskDecision.created_at))
        .all()
    )


@router.post("/review-queue/{payment_id}/resolve")
def resolve_risk_review(
    payment_id: str,
    data: RiskReviewResolveRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise NotFoundError("Payment", payment_id)

    decision = (
        db.query(RiskDecision)
        .filter(RiskDecision.payment_id == payment_id, RiskDecision.resolution_action == None)
        .first()
    )

    if not decision:
        raise SwitchException("NO_PENDING_REVIEW", "No pending risk review found for this payment.")

    decision.resolution_action = data.action
    decision.resolution_notes = data.notes
    decision.resolved_by_user_id = admin_user.id
    decision.resolved_at = datetime.now(timezone.utc)

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

    if data.action.upper() == "APPROVE":
        payment.status = PaymentStatus.SUCCEEDED
        payment.error_code = None
        payment.error_message = None

        if hold and customer_account:
            hold.status = HoldStatus.CAPTURED
            hold.resolved_at = datetime.now(timezone.utc)
            customer_account.balance_paise -= payment.amount_paise

        ledger_service.post_payment_capture(db, payment)

        payment_service.add_payment_event(
            db,
            payment,
            event_type="RISK_REVIEW_APPROVED",
            from_status=PaymentStatus.PENDING.value,
            to_status=PaymentStatus.SUCCEEDED.value,
            details=f"Compliance review approved by admin. {data.notes or ''}",
        )
    else:  # DECLINE
        payment.status = PaymentStatus.DECLINED
        payment.error_code = "RISK_REVIEW_DECLINED"
        payment.error_message = f"Transaction declined after risk investigation: {data.notes or 'Suspected fraudulent pattern'}"

        if hold and customer_account:
            hold.status = HoldStatus.RELEASED
            hold.resolved_at = datetime.now(timezone.utc)
            customer_account.available_balance_paise += payment.amount_paise

        payment_service.add_payment_event(
            db,
            payment,
            event_type="RISK_REVIEW_DECLINED",
            from_status=PaymentStatus.PENDING.value,
            to_status=PaymentStatus.DECLINED.value,
            details=payment.error_message,
        )

    db.commit()
    return {"message": f"Payment risk review resolved with {data.action.upper()}"}
