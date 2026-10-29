import json
import logging
from sqlalchemy.orm import Session
from app.models.job import BackgroundJob, JobType
from app.models.payment import Payment, PaymentStatus
from app.services import payment_service

logger = logging.getLogger("switch.worker.handlers")


def handle_job(db: Session, job: BackgroundJob) -> None:
    payload = json.loads(job.payload) if job.payload else {}

    if job.job_type == JobType.PROCESS_DELAYED_PAYMENT:
        payment_id = payload.get("payment_id")
        if payment_id:
            logger.info(f"Processing delayed payment resolution for {payment_id}")
            payment_service.resolve_pending_payment(db, payment_id)

    elif job.job_type == JobType.NEFT_BATCH_PROCESS:
        payment_id = payload.get("payment_id")
        if payment_id:
            logger.info(f"Resolving NEFT batch for payment {payment_id}")
            payment_service.resolve_pending_payment(db, payment_id)

    elif job.job_type == JobType.SETTLEMENT_PAYOUT_EXECUTE:
        # Additional async payout batch execution if needed
        pass

    elif job.job_type == JobType.RECONCILIATION_EXECUTE:
        pass

    elif job.job_type == JobType.REFUND_EXECUTE:
        pass

    db.flush()
