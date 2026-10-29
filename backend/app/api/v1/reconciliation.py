from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models.reconciliation import (
    ReconciliationRun,
    ReconciliationException,
    RecExceptionStatus,
)
from app.models.user import User
from app.schemas.reconciliation import (
    RecRunCreateRequest,
    RecRunResponse,
    RecExceptionResponse,
    RecExceptionResolveRequest,
)
from app.services import reconciliation_service
from app.api.deps import require_admin
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/reconciliation", tags=["Reconciliation"])


@router.post("/run", response_model=RecRunResponse, status_code=status.HTTP_201_CREATED)
def trigger_reconciliation_run(
    data: RecRunCreateRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    run = reconciliation_service.run_three_way_reconciliation(
        db=db,
        admin_user=admin_user,
        period_start=data.period_start,
        period_end=data.period_end,
        bank_id=data.bank_id,
    )
    db.commit()
    db.refresh(run)
    return run


@router.get("/runs", response_model=List[RecRunResponse])
def list_reconciliation_runs(
    limit: int = Query(50, ge=1, le=100),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return db.query(ReconciliationRun).order_by(desc(ReconciliationRun.created_at)).limit(limit).all()


@router.get("/runs/{run_id}", response_model=RecRunResponse)
def get_reconciliation_run(
    run_id: str,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    run = db.query(ReconciliationRun).filter(ReconciliationRun.id == run_id).first()
    if not run:
        raise NotFoundError("ReconciliationRun", run_id)
    return run


@router.get("/exceptions", response_model=List[RecExceptionResponse])
def list_exceptions(
    status_filter: Optional[RecExceptionStatus] = None,
    limit: int = Query(50, ge=1, le=100),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(ReconciliationException)
    if status_filter:
        query = query.filter(ReconciliationException.status == status_filter)
    return query.order_by(desc(ReconciliationException.created_at)).limit(limit).all()


@router.post("/exceptions/{exception_id}/resolve", response_model=RecExceptionResponse)
def resolve_exception(
    exception_id: str,
    data: RecExceptionResolveRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    exc = reconciliation_service.resolve_reconciliation_exception(
        db, exception_id, admin_user, data.resolution_notes, data.mark_as
    )
    db.commit()
    db.refresh(exc)
    return exc
