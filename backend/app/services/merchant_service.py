import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models.merchant import Merchant, MerchantMembership, MerchantStatus
from app.models.user import User, UserRole
from app.schemas.merchant import MerchantOnboardingRequest, MerchantReviewRequest, MerchantUpdateRequest
from app.core.exceptions import NotFoundError, PermissionDeniedError, SwitchException
from app.services import audit_service


def onboard_merchant(db: Session, user: User, data: MerchantOnboardingRequest) -> Merchant:
    # Check if merchant with contact email already exists
    existing = db.query(Merchant).filter(Merchant.contact_email == data.contact_email).first()
    if existing:
        raise SwitchException("MERCHANT_EXISTS", f"Merchant with contact email '{data.contact_email}' already exists.")

    merchant = Merchant(
        id=str(uuid.uuid4()),
        business_name=data.business_name,
        contact_email=data.contact_email,
        business_category=data.business_category,
        settlement_account_ref=data.settlement_account_ref,
        supported_methods=data.supported_methods or "UPI,CARD,NEFT,RTGS",
        fee_percentage_bps=data.fee_percentage_bps if data.fee_percentage_bps is not None else 150,
        fee_flat_paise=data.fee_flat_paise or 0,
        status=MerchantStatus.PENDING,
    )
    db.add(merchant)
    db.flush()

    membership = MerchantMembership(
        id=str(uuid.uuid4()),
        user_id=user.id,
        merchant_id=merchant.id,
        role_in_merchant="OWNER",
    )
    db.add(membership)
    db.flush()

    audit_service.log_audit_event(
        db,
        action="MERCHANT_ONBOARDED",
        entity_type="MERCHANT",
        entity_id=merchant.id,
        user_id=user.id,
        changes={"business_name": merchant.business_name, "status": merchant.status.value},
    )

    return merchant


def review_merchant(db: Session, admin_user: User, merchant_id: str, data: MerchantReviewRequest) -> Merchant:
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        raise NotFoundError("Merchant", merchant_id)

    merchant.status = data.status
    merchant.rejection_reason = data.rejection_reason
    if data.status == MerchantStatus.APPROVED:
        merchant.approved_at = datetime.now(timezone.utc)

    audit_service.log_audit_event(
        db,
        action="MERCHANT_REVIEWED",
        entity_type="MERCHANT",
        entity_id=merchant.id,
        user_id=admin_user.id,
        changes={"status": data.status.value, "reason": data.rejection_reason},
    )

    db.flush()
    return merchant


def update_merchant(db: Session, merchant_id: str, data: MerchantUpdateRequest, actor: User) -> Merchant:
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        raise NotFoundError("Merchant", merchant_id)

    # Ownership check
    if actor.role != UserRole.ADMIN:
        membership = [m for m in actor.merchant_memberships if m.merchant_id == merchant_id]
        if not membership:
            raise PermissionDeniedError("You do not have permission to manage this merchant.")

    if data.business_name is not None:
        merchant.business_name = data.business_name
    if data.contact_email is not None:
        merchant.contact_email = data.contact_email
    if data.settlement_account_ref is not None:
        merchant.settlement_account_ref = data.settlement_account_ref
    if data.supported_methods is not None:
        merchant.supported_methods = data.supported_methods
    if data.fee_percentage_bps is not None and actor.role == UserRole.ADMIN:
        merchant.fee_percentage_bps = data.fee_percentage_bps
    if data.fee_flat_paise is not None and actor.role == UserRole.ADMIN:
        merchant.fee_flat_paise = data.fee_flat_paise

    db.flush()
    return merchant
