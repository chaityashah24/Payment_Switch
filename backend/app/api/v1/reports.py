import csv
import io
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app.models.refund import Refund, RefundStatus
from app.models.merchant import Merchant
from app.models.user import User, UserRole
from app.api.deps import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports & Dashboards"])


@router.get("/dashboard")
def get_dashboard_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Payment)

    merchant_id = None
    if current_user.role == UserRole.CUSTOMER:
        query = query.filter(Payment.customer_id == current_user.id)
    elif current_user.role == UserRole.MERCHANT:
        merchant_ids = [m.merchant_id for m in current_user.merchant_memberships]
        query = query.filter(Payment.merchant_id.in_(merchant_ids))
        if merchant_ids:
            merchant_id = merchant_ids[0]

    all_payments = query.all()
    total_count = len(all_payments)
    succeeded_payments = [p for p in all_payments if p.status == PaymentStatus.SUCCEEDED]
    success_count = len(succeeded_payments)

    success_rate = (success_count / total_count * 100) if total_count > 0 else 100.0

    total_volume_paise = sum(p.amount_paise for p in succeeded_payments)
    total_fee_paise = sum(p.calculated_fee_paise for p in succeeded_payments)
    net_payable_paise = total_volume_paise - total_fee_paise

    # Method breakdown
    method_counts = {}
    for p in all_payments:
        m = p.payment_method.value
        method_counts[m] = method_counts.get(m, 0) + 1

    method_distribution = [
        {"method": k, "count": v} for k, v in method_counts.items()
    ]

    # Status counts
    status_counts = {}
    for p in all_payments:
        s = p.status.value
        status_counts[s] = status_counts.get(s, 0) + 1

    status_distribution = [
        {"status": k, "count": v} for k, v in status_counts.items()
    ]

    return {
        "total_transactions": total_count,
        "succeeded_count": success_count,
        "success_rate_percent": round(success_rate, 2),
        "total_volume_paise": total_volume_paise,
        "total_volume_inr": f"₹{total_volume_paise / 100:,.2f}",
        "total_fee_paise": total_fee_paise,
        "total_fee_inr": f"₹{total_fee_paise / 100:,.2f}",
        "net_payable_paise": net_payable_paise,
        "net_payable_inr": f"₹{net_payable_paise / 100:,.2f}",
        "method_distribution": method_distribution,
        "status_distribution": status_distribution,
    }


@router.get("/transactions/export")
def export_transactions_csv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Payment)
    if current_user.role == UserRole.CUSTOMER:
        query = query.filter(Payment.customer_id == current_user.id)
    elif current_user.role == UserRole.MERCHANT:
        merchant_ids = [m.merchant_id for m in current_user.merchant_memberships]
        query = query.filter(Payment.merchant_id.in_(merchant_ids))

    payments = query.order_by(Payment.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Payment ID",
        "Timestamp (UTC)",
        "Merchant",
        "Method",
        "Amount (INR)",
        "Fee (INR)",
        "Net (INR)",
        "Status",
        "Bank Reference",
        "Error Message",
    ])

    for p in payments:
        writer.writerow([
            p.id,
            p.created_at.isoformat(),
            p.merchant.business_name if p.merchant else p.merchant_id,
            p.payment_method.value,
            f"{p.amount_paise / 100:.2f}",
            f"{p.calculated_fee_paise / 100:.2f}",
            f"{(p.amount_paise - p.calculated_fee_paise) / 100:.2f}",
            p.status.value,
            p.bank_reference or "",
            p.error_message or "",
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions_export.csv"},
    )
