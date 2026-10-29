from datetime import datetime, timezone, timedelta
from app.models.reconciliation import RecRunStatus, RecExceptionStatus
from app.services import reconciliation_service


def test_reconciliation_workflow(db, test_admin):
    period_start = datetime.now(timezone.utc) - timedelta(days=7)
    period_end = datetime.now(timezone.utc) + timedelta(days=1)

    rec_run = reconciliation_service.run_three_way_reconciliation(
        db=db,
        admin_user=test_admin,
        period_start=period_start,
        period_end=period_end,
    )

    assert rec_run.status == RecRunStatus.COMPLETED
    assert rec_run.run_reference is not None

    # If exceptions generated, verify resolve
    if rec_run.exceptions:
        exc = rec_run.exceptions[0]
        resolved = reconciliation_service.resolve_reconciliation_exception(
            db=db,
            exception_id=exc.id,
            admin_user=test_admin,
            resolution_notes="Discrepancy investigated and resolved with audit verification",
        )
        assert resolved.status == RecExceptionStatus.RESOLVED
