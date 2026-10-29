import pytest
from app.models.ledger import AccountClassification, PostingDirection, JournalEntryType
from app.services import ledger_service
from app.core.exceptions import LedgerImbalanceError


def test_balanced_ledger_posting(db):
    acc_asset = ledger_service.get_or_create_account(
        db, "TEST_ASSET_01", "Test Asset Account", AccountClassification.ASSET
    )
    acc_liability = ledger_service.get_or_create_account(
        db, "TEST_LIAB_01", "Test Liability Account", AccountClassification.LIABILITY
    )

    lines = [
        (acc_asset, PostingDirection.DEBIT, 50000),
        (acc_liability, PostingDirection.CREDIT, 50000),
    ]

    entry = ledger_service.post_journal_entry(
        db=db,
        entry_number="JE-TEST-BALANCED-01",
        entry_type=JournalEntryType.PAYMENT_CAPTURE,
        source_type="TEST",
        source_id="test_id_1",
        description="Balanced entry test",
        lines=lines,
    )
    assert entry.status == "POSTED"

    # Materialized balances check
    assert acc_asset.balance_paise == 50000
    assert acc_liability.balance_paise == 50000

    # Invariants verification check
    integrity = ledger_service.verify_ledger_invariants(db)
    assert integrity["is_balanced"] is True


def test_imbalanced_ledger_posting_rejection(db):
    acc_asset = ledger_service.get_or_create_account(
        db, "TEST_ASSET_02", "Test Asset 2", AccountClassification.ASSET
    )
    acc_liability = ledger_service.get_or_create_account(
        db, "TEST_LIAB_02", "Test Liability 2", AccountClassification.LIABILITY
    )

    lines = [
        (acc_asset, PostingDirection.DEBIT, 10000),
        (acc_liability, PostingDirection.CREDIT, 8000),  # Imbalanced by 2000 paise!
    ]

    with pytest.raises(LedgerImbalanceError):
        ledger_service.post_journal_entry(
            db=db,
            entry_number="JE-TEST-IMBALANCED",
            entry_type=JournalEntryType.PAYMENT_CAPTURE,
            source_type="TEST",
            source_id="test_id_2",
            description="Imbalanced entry should raise",
            lines=lines,
        )
