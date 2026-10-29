from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.merchant import Merchant, MerchantStatus
from app.models.user import User, UserRole
from app.schemas.merchant import (
    MerchantOnboardingRequest,
    MerchantUpdateRequest,
    MerchantReviewRequest,
    MerchantResponse,
)
from app.services import merchant_service
from app.api.deps import get_current_user, require_admin, require_merchant
from app.core.exceptions import NotFoundError, PermissionDeniedError

router = APIRouter(prefix="/merchants", tags=["Merchants"])


@router.get("", response_model=List[MerchantResponse])
def list_merchants(
    status_filter: Optional[MerchantStatus] = None,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Merchant)
    # If not admin, customers and public only see APPROVED merchants
    if not current_user or current_user.role != UserRole.ADMIN:
        query = query.filter(Merchant.status == MerchantStatus.APPROVED)
    elif status_filter:
        query = query.filter(Merchant.status == status_filter)

    return query.order_by(Merchant.created_at.desc()).all()


@router.post("/onboard", response_model=MerchantResponse, status_code=status.HTTP_201_CREATED)
def onboard_merchant(
    data: MerchantOnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return merchant_service.onboard_merchant(db, current_user, data)


@router.get("/me", response_model=MerchantResponse)
def get_my_merchant_profile(
    current_user: User = Depends(require_merchant),
    db: Session = Depends(get_db),
):
    if not current_user.merchant_memberships:
        raise NotFoundError("Merchant", "current_user")
    return current_user.merchant_memberships[0].merchant


@router.get("/{merchant_id}", response_model=MerchantResponse)
def get_merchant_by_id(
    merchant_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        raise NotFoundError("Merchant", merchant_id)

    # If merchant is not approved, only admin or member can see
    if merchant.status != MerchantStatus.APPROVED and current_user.role != UserRole.ADMIN:
        membership = [m for m in current_user.merchant_memberships if m.merchant_id == merchant_id]
        if not membership:
            raise PermissionDeniedError("Cannot view unapproved merchant.")

    return merchant


@router.put("/{merchant_id}", response_model=MerchantResponse)
def update_merchant(
    merchant_id: str,
    data: MerchantUpdateRequest,
    current_user: User = Depends(require_merchant),
    db: Session = Depends(get_db),
):
    return merchant_service.update_merchant(db, merchant_id, data, current_user)


@router.post("/{merchant_id}/review", response_model=MerchantResponse)
def review_merchant(
    merchant_id: str,
    data: MerchantReviewRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return merchant_service.review_merchant(db, admin_user, merchant_id, data)
