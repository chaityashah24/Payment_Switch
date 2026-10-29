from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models.refund import Refund
from app.models.user import User, UserRole
from app.schemas.refund import RefundCreateRequest, RefundResponse
from app.services import refund_service
from app.api.deps import require_merchant, get_current_user
from app.core.exceptions import NotFoundError, PermissionDeniedError

router = APIRouter(prefix="/refunds", tags=["Refunds"])


@router.post("", response_model=RefundResponse, status_code=status.HTTP_201_CREATED)
def issue_refund(
    data: RefundCreateRequest,
    merchant_user: User = Depends(require_merchant),
    db: Session = Depends(get_db),
):
    refund = refund_service.create_refund(
        db=db,
        merchant_user=merchant_user,
        payment_id=data.payment_id,
        amount_paise=data.amount_paise,
        reason=data.reason,
        idempotency_key=data.idempotency_key,
    )
    db.commit()
    db.refresh(refund)
    return refund


@router.get("", response_model=List[RefundResponse])
def list_refunds(
    merchant_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Refund)
    if current_user.role == UserRole.MERCHANT:
        user_merchants = [m.merchant_id for m in current_user.merchant_memberships]
        query = query.filter(Refund.merchant_id.in_(user_merchants))
    elif merchant_id:
        query = query.filter(Refund.merchant_id == merchant_id)

    return query.order_by(desc(Refund.created_at)).limit(limit).all()


@router.get("/{refund_id}", response_model=RefundResponse)
def get_refund_details(
    refund_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    refund = db.query(Refund).filter(Refund.id == refund_id).first()
    if not refund:
        raise NotFoundError("Refund", refund_id)

    if current_user.role == UserRole.MERCHANT:
        user_merchants = {m.merchant_id for m in current_user.merchant_memberships}
        if refund.merchant_id not in user_merchants:
            raise PermissionDeniedError("Cannot access this refund.")

    return refund
