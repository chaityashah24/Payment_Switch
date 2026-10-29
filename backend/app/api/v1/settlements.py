from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models.settlement import SettlementBatch, SettlementItem, SettlementAllocation
from app.models.user import User, UserRole
from app.schemas.settlement import (
    SettlementPreviewResponse,
    SettlementBatchResponse,
    SettlementItemResponse,
    SettlementBatchCreateRequest,
)
from app.services import settlement_service
from app.api.deps import require_admin, require_merchant, get_current_user
from app.core.exceptions import NotFoundError, PermissionDeniedError

router = APIRouter(prefix="/settlements", tags=["Settlement"])


@router.get("/preview", response_model=SettlementPreviewResponse)
def get_settlement_preview(
    cutoff_time: Optional[datetime] = None,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return settlement_service.calculate_settlement_preview(db, cutoff_time)


@router.post("/batch", response_model=SettlementBatchResponse, status_code=status.HTTP_201_CREATED)
def execute_settlement_batch(
    data: SettlementBatchCreateRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    batch = settlement_service.create_and_execute_settlement_batch(
        db, admin_user, data.cutoff_timestamp
    )
    db.commit()
    db.refresh(batch)
    return batch


@router.get("/batches", response_model=List[SettlementBatchResponse])
def list_settlement_batches(
    limit: int = Query(50, ge=1, le=100),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return db.query(SettlementBatch).order_by(desc(SettlementBatch.created_at)).limit(limit).all()


@router.get("/batches/{batch_id}", response_model=SettlementBatchResponse)
def get_settlement_batch(
    batch_id: str,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    batch = db.query(SettlementBatch).filter(SettlementBatch.id == batch_id).first()
    if not batch:
        raise NotFoundError("SettlementBatch", batch_id)
    return batch


@router.post("/items/{item_id}/retry", response_model=SettlementItemResponse)
def retry_failed_payout(
    item_id: str,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    item = settlement_service.retry_failed_payout(db, item_id, admin_user)
    db.commit()
    db.refresh(item)
    return item


@router.get("/merchant", response_model=List[SettlementItemResponse])
def get_merchant_settlement_items(
    merchant_user: User = Depends(require_merchant),
    db: Session = Depends(get_db),
):
    merchant_ids = [m.merchant_id for m in merchant_user.merchant_memberships]
    items = (
        db.query(SettlementItem)
        .filter(SettlementItem.merchant_id.in_(merchant_ids))
        .order_by(desc(SettlementItem.created_at))
        .all()
    )
    return items
