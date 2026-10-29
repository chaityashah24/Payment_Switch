import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.settlement import (
    SettlementBatch,
    SettlementItem,
    SettlementAllocation,
    BatchStatus,
    SettlementItemStatus,
)
from app.models.payment import Payment, PaymentStatus
from app.models.refund import Refund, RefundStatus
from app.models.merchant import Merchant
from app.models.user import User
from app.models.scenario import SimulationScenario
from app.core.exceptions import NotFoundError, SwitchException
from app.services import ledger_service, audit_service


def calculate_settlement_preview(db: Session, cutoff_time: Optional[datetime] = None) -> Dict[str, Any]:
    if not cutoff_time:
        cutoff_time = datetime.now(timezone.utc)

    # 1. Unallocated captured payments
    eligible_payments = (
        db.query(Payment)
        .filter(
            Payment.status == PaymentStatus.SUCCEEDED,
            Payment.settled_item_id == None,
            Payment.created_at <= cutoff_time,
        )
        .all()
    )

    # 2. Unallocated succeeded refunds
    allocated_refund_ids = (
        db.query(SettlementAllocation.refund_id)
        .filter(SettlementAllocation.refund_id != None)
        .all()
    )
    allocated_refund_ids = {r[0] for r in allocated_refund_ids}

    eligible_refunds = (
        db.query(Refund)
        .filter(
            Refund.status == RefundStatus.SUCCEEDED,
            Refund.created_at <= cutoff_time,
        )
        .all()
    )
    eligible_refunds = [r for r in eligible_refunds if r.id not in allocated_refund_ids]

    # Group by merchant
    merchants_map: Dict[str, Dict[str, Any]] = {}
    for p in eligible_payments:
        if p.merchant_id not in merchants_map:
            merchant = db.query(Merchant).filter(Merchant.id == p.merchant_id).first()
            merchants_map[p.merchant_id] = {
                "merchant_id": p.merchant_id,
                "merchant_name": merchant.business_name if merchant else "Unknown",
                "payments": [],
                "refunds": [],
                "gross_paise": 0,
                "fee_paise": 0,
                "refund_paise": 0,
                "net_payable_paise": 0,
            }
        merchants_map[p.merchant_id]["payments"].append(p)
        merchants_map[p.merchant_id]["gross_paise"] += p.amount_paise
        merchants_map[p.merchant_id]["fee_paise"] += p.calculated_fee_paise

    for r in eligible_refunds:
        if r.merchant_id not in merchants_map:
            merchant = db.query(Merchant).filter(Merchant.id == r.merchant_id).first()
            merchants_map[r.merchant_id] = {
                "merchant_id": r.merchant_id,
                "merchant_name": merchant.business_name if merchant else "Unknown",
                "payments": [],
                "refunds": [],
                "gross_paise": 0,
                "fee_paise": 0,
                "refund_paise": 0,
                "net_payable_paise": 0,
            }
        merchants_map[r.merchant_id]["refunds"].append(r)
        # Deduct net refund amount (refund - fee refund)
        merchants_map[r.merchant_id]["refund_paise"] += (r.amount_paise - r.fee_refund_paise)

    preview_items = []
    tot_gross = 0
    tot_fee = 0
    tot_refund = 0
    tot_net = 0

    for m_id, data in merchants_map.items():
        net = data["gross_paise"] - data["fee_paise"] - data["refund_paise"]
        data["net_payable_paise"] = net
        tot_gross += data["gross_paise"]
        tot_fee += data["fee_paise"]
        tot_refund += data["refund_paise"]
        tot_net += net

        preview_items.append({
            "merchant_id": m_id,
            "merchant_name": data["merchant_name"],
            "eligible_payment_count": len(data["payments"]),
            "gross_amount_paise": data["gross_paise"],
            "fee_amount_paise": data["fee_paise"],
            "eligible_refund_count": len(data["refunds"]),
            "refund_amount_paise": data["refund_paise"],
            "net_payable_paise": net,
        })

    return {
        "cutoff_timestamp": cutoff_time,
        "merchants": preview_items,
        "total_gross_paise": tot_gross,
        "total_fee_paise": tot_fee,
        "total_refund_paise": tot_refund,
        "total_net_payable_paise": tot_net,
    }


def create_and_execute_settlement_batch(
    db: Session,
    admin_user: User,
    cutoff_time: Optional[datetime] = None,
) -> SettlementBatch:
    if not cutoff_time:
        cutoff_time = datetime.now(timezone.utc)

    # 1. Check if scenario SETTLEMENT_PAYOUT_FAILURE is active
    scenario = db.query(SimulationScenario).filter(
        SimulationScenario.name == "SETTLEMENT_PAYOUT_FAILURE",
        SimulationScenario.is_active == True,
    ).first()

    # 2. Compute preview
    preview = calculate_settlement_preview(db, cutoff_time)
    if not preview["merchants"]:
        raise SwitchException("NO_ELIGIBLE_TRANSACTIONS", "No eligible payments or refunds for settlement up to cutoff timestamp.")

    batch_ref = f"SETTLE-BATCH-{int(cutoff_time.timestamp())}"
    batch = SettlementBatch(
        id=str(uuid.uuid4()),
        batch_reference=batch_ref,
        cutoff_timestamp=cutoff_time,
        status=BatchStatus.PROCESSING,
        total_gross_paise=preview["total_gross_paise"],
        total_fee_paise=preview["total_fee_paise"],
        total_refund_adjustment_paise=preview["total_refund_paise"],
        total_net_paise=preview["total_net_payable_paise"],
    )
    db.add(batch)
    db.flush()

    has_failures = False

    for item_data in preview["merchants"]:
        m_id = item_data["merchant_id"]
        payout_ref = f"PAYOUT-{uuid.uuid4().hex[:8].upper()}"

        item = SettlementItem(
            id=str(uuid.uuid4()),
            settlement_batch_id=batch.id,
            merchant_id=m_id,
            gross_amount_paise=item_data["gross_amount_paise"],
            fee_amount_paise=item_data["fee_amount_paise"],
            refund_amount_paise=item_data["refund_amount_paise"],
            net_payable_paise=item_data["net_payable_paise"],
            payout_reference=payout_ref,
            status=SettlementItemStatus.PENDING,
        )
        db.add(item)
        db.flush()

        # Allocate payments
        m_payments = (
            db.query(Payment)
            .filter(
                Payment.merchant_id == m_id,
                Payment.status == PaymentStatus.SUCCEEDED,
                Payment.settled_item_id == None,
                Payment.created_at <= cutoff_time,
            )
            .all()
        )
        for p in m_payments:
            p.settled_item_id = item.id
            alloc = SettlementAllocation(
                id=str(uuid.uuid4()),
                settlement_item_id=item.id,
                payment_id=p.id,
                allocation_type="PAYMENT",
                amount_paise=p.amount_paise,
            )
            db.add(alloc)

        # Allocate refunds
        allocated_refund_ids = (
            db.query(SettlementAllocation.refund_id)
            .filter(SettlementAllocation.refund_id != None)
            .all()
        )
        allocated_refund_ids = {r[0] for r in allocated_refund_ids}
        m_refunds = (
            db.query(Refund)
            .filter(
                Refund.merchant_id == m_id,
                Refund.status == RefundStatus.SUCCEEDED,
                Refund.created_at <= cutoff_time,
            )
            .all()
        )
        for r in m_refunds:
            if r.id not in allocated_refund_ids:
                alloc = SettlementAllocation(
                    id=str(uuid.uuid4()),
                    settlement_item_id=item.id,
                    refund_id=r.id,
                    allocation_type="REFUND",
                    amount_paise=r.amount_paise,
                )
                db.add(alloc)

        db.flush()

        # Payout Execution simulation
        if scenario:
            # Payout fails simulation
            item.status = SettlementItemStatus.FAILED
            item.last_error = "Simulated bank payout API returned HTTP 500: Beneficiary nodal account unreachable"
            has_failures = True
        else:
            # Payout succeeds: Post ledger entry
            item.status = SettlementItemStatus.PAID
            ledger_service.post_settlement_payout(db, item)

    if has_failures:
        batch.status = BatchStatus.PARTIALLY_FAILED
    else:
        batch.status = BatchStatus.COMPLETED
        batch.completed_at = datetime.now(timezone.utc)

    audit_service.log_audit_event(
        db,
        action="SETTLEMENT_BATCH_EXECUTED",
        entity_type="SETTLEMENT_BATCH",
        entity_id=batch.id,
        user_id=admin_user.id,
        changes={"batch_ref": batch.batch_reference, "status": batch.status.value},
    )

    db.flush()
    return batch


def retry_failed_payout(db: Session, settlement_item_id: str, admin_user: User) -> SettlementItem:
    """Retries a failed payout without re-selecting transactions."""
    item = db.query(SettlementItem).filter(SettlementItem.id == settlement_item_id).first()
    if not item:
        raise NotFoundError("SettlementItem", settlement_item_id)

    if item.status != SettlementItemStatus.FAILED:
        raise SwitchException("ITEM_NOT_FAILED", f"Only FAILED settlement payouts can be retried. Current status is {item.status.value}")

    item.retry_count += 1
    # Retry succeeds: post ledger
    item.status = SettlementItemStatus.PAID
    item.last_error = None
    ledger_service.post_settlement_payout(db, item)

    # Check if parent batch has any remaining failed items
    batch = item.batch
    failed_items = (
        db.query(SettlementItem)
        .filter(
            SettlementItem.settlement_batch_id == batch.id,
            SettlementItem.status == SettlementItemStatus.FAILED,
        )
        .count()
    )
    if failed_items == 0:
        batch.status = BatchStatus.COMPLETED
        batch.completed_at = datetime.now(timezone.utc)

    audit_service.log_audit_event(
        db,
        action="SETTLEMENT_PAYOUT_RETRIED",
        entity_type="SETTLEMENT_ITEM",
        entity_id=item.id,
        user_id=admin_user.id,
        changes={"retry_count": item.retry_count, "new_status": "PAID"},
    )

    db.flush()
    return item
