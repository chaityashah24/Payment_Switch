from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models.payment import PaymentRoute
from app.models.account import SimulatedBank
from app.models.job import BackgroundJob
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogResponse
from app.services import ledger_service
from app.api.deps import require_admin
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/admin", tags=["Admin System Management"])


@router.get("/routes")
def list_payment_routes(admin_user=Depends(require_admin), db: Session = Depends(get_db)):
    routes = db.query(PaymentRoute).all()
    return [
        {
            "id": r.id,
            "payment_method": r.payment_method.value,
            "bank_id": r.bank_id,
            "bank_name": r.bank.name if r.bank else "Unknown",
            "is_enabled": r.is_enabled,
            "priority": r.priority,
            "fee_bps": r.fee_bps,
        }
        for r in routes
    ]


@router.put("/routes/{route_id}/toggle")
def toggle_route(route_id: str, admin_user=Depends(require_admin), db: Session = Depends(get_db)):
    route = db.query(PaymentRoute).filter(PaymentRoute.id == route_id).first()
    if not route:
        raise NotFoundError("PaymentRoute", route_id)
    route.is_enabled = not route.is_enabled
    db.commit()
    return {"id": route.id, "is_enabled": route.is_enabled}


@router.get("/banks")
def list_banks_admin(admin_user=Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(SimulatedBank).all()


@router.put("/banks/{bank_id}/toggle")
def toggle_bank_availability(bank_id: str, admin_user=Depends(require_admin), db: Session = Depends(get_db)):
    bank = db.query(SimulatedBank).filter(SimulatedBank.id == bank_id).first()
    if not bank:
        raise NotFoundError("SimulatedBank", bank_id)
    bank.is_available = not bank.is_available
    db.commit()
    return {"id": bank.id, "code": bank.code, "is_available": bank.is_available}


@router.get("/jobs")
def list_background_jobs(
    limit: int = Query(50, ge=1, le=100),
    admin_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    jobs = db.query(BackgroundJob).order_by(desc(BackgroundJob.created_at)).limit(limit).all()
    return [
        {
            "id": j.id,
            "job_type": j.job_type.value,
            "status": j.status.value,
            "retry_count": j.retry_count,
            "payload": j.payload,
            "last_error": j.last_error,
            "created_at": j.created_at,
            "updated_at": j.updated_at,
        }
        for j in jobs
    ]


@router.get("/ledger/integrity")
def get_ledger_integrity(admin_user=Depends(require_admin), db: Session = Depends(get_db)):
    return ledger_service.verify_ledger_invariants(db)


@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    admin_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    return db.query(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit).all()
