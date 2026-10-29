import uuid
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.ledger import (
    LedgerAccount,
    JournalEntry,
    JournalLine,
    AccountClassification,
    PostingDirection,
    JournalEntryType,
)
from app.models.payment import Payment
from app.models.refund import Refund
from app.models.settlement import SettlementItem
from app.core.exceptions import LedgerImbalanceError


def get_or_create_account(
    db: Session,
    code: str,
    name: str,
    classification: AccountClassification,
    owner_type: str = "SYSTEM",
    owner_id: str = None,
    currency: str = "INR",
) -> LedgerAccount:
    account = db.query(LedgerAccount).filter(LedgerAccount.code == code).first()
    if not account:
        account = LedgerAccount(
            id=str(uuid.uuid4()),
            code=code,
            name=name,
            classification=classification,
            currency=currency,
            balance_paise=0,
            owner_type=owner_type,
            owner_id=owner_id,
        )
        db.add(account)
        db.flush()
    return account


def post_journal_entry(
    db: Session,
    entry_number: str,
    entry_type: JournalEntryType,
    source_type: str,
    source_id: str,
    description: str,
    lines: List[Tuple[LedgerAccount, PostingDirection, int]],  # (account, direction, amount_paise)
) -> JournalEntry:
    # Check debits == credits
    total_debits = sum(amount for _, direction, amount in lines if direction == PostingDirection.DEBIT)
    total_credits = sum(amount for _, direction, amount in lines if direction == PostingDirection.CREDIT)

    if total_debits != total_credits:
        raise LedgerImbalanceError(total_debits, total_credits)

    entry = JournalEntry(
        id=str(uuid.uuid4()),
        entry_number=entry_number,
        entry_type=entry_type,
        source_type=source_type,
        source_id=source_id,
        description=description,
        status="POSTED",
    )
    db.add(entry)
    db.flush()

    for account, direction, amount in lines:
        line = JournalLine(
            id=str(uuid.uuid4()),
            journal_entry_id=entry.id,
            ledger_account_id=account.id,
            direction=direction,
            amount_paise=amount,
            currency=account.currency,
        )
        db.add(line)

        # Update materialized balance atomically
        if account.classification in [AccountClassification.ASSET, AccountClassification.EXPENSE]:
            if direction == PostingDirection.DEBIT:
                account.balance_paise += amount
            else:
                account.balance_paise -= amount
        else:  # LIABILITY, EQUITY, REVENUE
            if direction == PostingDirection.CREDIT:
                account.balance_paise += amount
            else:
                account.balance_paise -= amount

    db.flush()
    return entry


def post_payment_capture(db: Session, payment: Payment) -> JournalEntry:
    """
    Standard Payment Capture Entry:
    DEBIT  CUSTOMER_FUNDS_HOLD: gross amount
    CREDIT MERCHANT_PAYABLE_{merchant_id}: gross - fee
    CREDIT FEE_REVENUE: fee
    """
    customer_hold_acc = get_or_create_account(
        db,
        code="CUSTOMER_FUNDS_HOLD",
        name="Customer Funds In Clearing",
        classification=AccountClassification.ASSET,
    )
    merchant_payable_acc = get_or_create_account(
        db,
        code=f"MERCHANT_PAYABLE_{payment.merchant_id}",
        name=f"Merchant Payable ({payment.merchant.business_name if payment.merchant else payment.merchant_id})",
        classification=AccountClassification.LIABILITY,
        owner_type="MERCHANT",
        owner_id=payment.merchant_id,
    )
    fee_revenue_acc = get_or_create_account(
        db,
        code="FEE_REVENUE",
        name="Platform Fee Revenue",
        classification=AccountClassification.REVENUE,
    )

    gross_amount = payment.amount_paise
    fee_amount = payment.calculated_fee_paise
    net_payable = gross_amount - fee_amount

    lines = [
        (customer_hold_acc, PostingDirection.DEBIT, gross_amount),
        (merchant_payable_acc, PostingDirection.CREDIT, net_payable),
    ]
    if fee_amount > 0:
        lines.append((fee_revenue_acc, PostingDirection.CREDIT, fee_amount))

    entry_num = f"JE-PAY-{payment.id[:8].upper()}"
    return post_journal_entry(
        db,
        entry_number=entry_num,
        entry_type=JournalEntryType.PAYMENT_CAPTURE,
        source_type="PAYMENT",
        source_id=payment.id,
        description=f"Capture for payment {payment.id} (Gross: {gross_amount}, Net: {net_payable}, Fee: {fee_amount})",
        lines=lines,
    )


def post_refund(db: Session, refund: Refund, payment: Payment) -> JournalEntry:
    """
    Refund Entry:
    DEBIT  MERCHANT_PAYABLE_{merchant_id}: net refund portion (refund_amount - fee_refund)
    DEBIT  FEE_REVENUE: fee_refund (if platform policy refunds fees proportionally)
    CREDIT CUSTOMER_FUNDS_HOLD: refund_amount
    """
    customer_hold_acc = get_or_create_account(
        db,
        code="CUSTOMER_FUNDS_HOLD",
        name="Customer Funds In Clearing",
        classification=AccountClassification.ASSET,
    )
    merchant_payable_acc = get_or_create_account(
        db,
        code=f"MERCHANT_PAYABLE_{payment.merchant_id}",
        name=f"Merchant Payable ({payment.merchant.business_name if payment.merchant else payment.merchant_id})",
        classification=AccountClassification.LIABILITY,
        owner_type="MERCHANT",
        owner_id=payment.merchant_id,
    )
    fee_revenue_acc = get_or_create_account(
        db,
        code="FEE_REVENUE",
        name="Platform Fee Revenue",
        classification=AccountClassification.REVENUE,
    )

    gross_refund = refund.amount_paise
    fee_refund = refund.fee_refund_paise
    merchant_debit = gross_refund - fee_refund

    lines = [
        (merchant_payable_acc, PostingDirection.DEBIT, merchant_debit),
        (customer_hold_acc, PostingDirection.CREDIT, gross_refund),
    ]
    if fee_refund > 0:
        lines.append((fee_revenue_acc, PostingDirection.DEBIT, fee_refund))

    entry_num = f"JE-REF-{refund.id[:8].upper()}"
    return post_journal_entry(
        db,
        entry_number=entry_num,
        entry_type=JournalEntryType.REFUND,
        source_type="REFUND",
        source_id=refund.id,
        description=f"Refund {refund.id} for payment {payment.id} (Amount: {gross_refund})",
        lines=lines,
    )


def post_settlement_payout(db: Session, item: SettlementItem) -> JournalEntry:
    """
    Settlement Payout Entry:
    DEBIT  MERCHANT_PAYABLE_{merchant_id}: net payable
    CREDIT SETTLEMENT_CLEARING: net payable
    """
    merchant_payable_acc = get_or_create_account(
        db,
        code=f"MERCHANT_PAYABLE_{item.merchant_id}",
        name=f"Merchant Payable ({item.merchant.business_name if item.merchant else item.merchant_id})",
        classification=AccountClassification.LIABILITY,
        owner_type="MERCHANT",
        owner_id=item.merchant_id,
    )
    settlement_clearing_acc = get_or_create_account(
        db,
        code="SETTLEMENT_CLEARING",
        name="Settlement Clearing Account",
        classification=AccountClassification.ASSET,
    )

    amount = item.net_payable_paise
    lines = [
        (merchant_payable_acc, PostingDirection.DEBIT, amount),
        (settlement_clearing_acc, PostingDirection.CREDIT, amount),
    ]

    entry_num = f"JE-SETTLE-{item.id[:8].upper()}"
    return post_journal_entry(
        db,
        entry_number=entry_num,
        entry_type=JournalEntryType.SETTLEMENT_PAYOUT,
        source_type="SETTLEMENT_ITEM",
        source_id=item.id,
        description=f"Settlement payout item {item.id} to {item.merchant_id} (Net: {amount})",
        lines=lines,
    )


def verify_ledger_invariants(db: Session) -> Dict[str, Any]:
    """Consistency check across all entries and accounts."""
    total_debits = (
        db.query(func.coalesce(func.sum(JournalLine.amount_paise), 0))
        .filter(JournalLine.direction == PostingDirection.DEBIT)
        .scalar()
    )
    total_credits = (
        db.query(func.coalesce(func.sum(JournalLine.amount_paise), 0))
        .filter(JournalLine.direction == PostingDirection.CREDIT)
        .scalar()
    )

    balanced = (total_debits == total_credits)
    return {
        "is_balanced": balanced,
        "total_debits_paise": total_debits,
        "total_credits_paise": total_credits,
        "difference_paise": total_debits - total_credits,
    }
