from typing import Set, Dict
from app.models.payment import PaymentStatus
from app.models.refund import RefundStatus
from app.models.settlement import BatchStatus, SettlementItemStatus
from app.models.reconciliation import RecRunStatus, RecExceptionStatus
from app.core.exceptions import InvalidStateTransitionError

# Valid transition graphs
PAYMENT_TRANSITIONS: Dict[PaymentStatus, Set[PaymentStatus]] = {
    PaymentStatus.CREATED: {
        PaymentStatus.AUTHENTICATION_REQUIRED,
        PaymentStatus.QUEUED,
        PaymentStatus.PROCESSING,
        PaymentStatus.PENDING,
        PaymentStatus.DECLINED,
        PaymentStatus.FAILED,
        PaymentStatus.CANCELLED,
    },
    PaymentStatus.AUTHENTICATION_REQUIRED: {
        PaymentStatus.PROCESSING,
        PaymentStatus.QUEUED,
        PaymentStatus.DECLINED,
        PaymentStatus.FAILED,
        PaymentStatus.CANCELLED,
    },
    PaymentStatus.QUEUED: {
        PaymentStatus.PROCESSING,
        PaymentStatus.CANCELLED,
        PaymentStatus.FAILED,
    },
    PaymentStatus.PROCESSING: {
        PaymentStatus.PENDING,
        PaymentStatus.SUCCEEDED,
        PaymentStatus.DECLINED,
        PaymentStatus.FAILED,
    },
    PaymentStatus.PENDING: {
        PaymentStatus.SUCCEEDED,
        PaymentStatus.DECLINED,
        PaymentStatus.FAILED,
    },
    # Terminal states (cannot transition further):
    PaymentStatus.SUCCEEDED: set(),
    PaymentStatus.DECLINED: set(),
    PaymentStatus.FAILED: set(),
    PaymentStatus.CANCELLED: set(),
}

REFUND_TRANSITIONS: Dict[RefundStatus, Set[RefundStatus]] = {
    RefundStatus.PENDING: {RefundStatus.SUCCEEDED, RefundStatus.FAILED},
    RefundStatus.SUCCEEDED: set(),
    RefundStatus.FAILED: set(),
}

SETTLEMENT_BATCH_TRANSITIONS: Dict[BatchStatus, Set[BatchStatus]] = {
    BatchStatus.CREATED: {BatchStatus.PROCESSING, BatchStatus.FAILED},
    BatchStatus.PROCESSING: {BatchStatus.COMPLETED, BatchStatus.PARTIALLY_FAILED, BatchStatus.FAILED},
    BatchStatus.COMPLETED: set(),
    BatchStatus.PARTIALLY_FAILED: {BatchStatus.PROCESSING, BatchStatus.COMPLETED},
    BatchStatus.FAILED: {BatchStatus.PROCESSING},
}

SETTLEMENT_ITEM_TRANSITIONS: Dict[SettlementItemStatus, Set[SettlementItemStatus]] = {
    SettlementItemStatus.PENDING: {SettlementItemStatus.PAID, SettlementItemStatus.FAILED},
    SettlementItemStatus.PAID: set(),
    SettlementItemStatus.FAILED: {SettlementItemStatus.PENDING, SettlementItemStatus.PAID},
}

REC_RUN_TRANSITIONS: Dict[RecRunStatus, Set[RecRunStatus]] = {
    RecRunStatus.IN_PROGRESS: {RecRunStatus.COMPLETED, RecRunStatus.FAILED},
    RecRunStatus.COMPLETED: set(),
    RecRunStatus.FAILED: set(),
}

REC_EXCEPTION_TRANSITIONS: Dict[RecExceptionStatus, Set[RecExceptionStatus]] = {
    RecExceptionStatus.OPEN: {RecExceptionStatus.INVESTIGATING, RecExceptionStatus.RESOLVED},
    RecExceptionStatus.INVESTIGATING: {RecExceptionStatus.RESOLVED, RecExceptionStatus.OPEN},
    RecExceptionStatus.RESOLVED: set(),
}


def validate_payment_transition(current: PaymentStatus, target: PaymentStatus) -> None:
    if current == target:
        return
    allowed = PAYMENT_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise InvalidStateTransitionError(current.value, target.value)


def validate_refund_transition(current: RefundStatus, target: RefundStatus) -> None:
    if current == target:
        return
    allowed = REFUND_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise InvalidStateTransitionError(current.value, target.value)
