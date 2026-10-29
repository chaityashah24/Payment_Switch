import time
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import SessionLocal
from app.models.job import BackgroundJob, JobStatus
from app.worker.handlers import handle_job

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("switch.worker")


class WorkerEngine:
    def __init__(self, worker_id: Optional[str] = None, poll_interval_seconds: float = 2.0):
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex[:6]}"
        self.poll_interval = poll_interval_seconds
        self.running = False

    def claim_next_job(self, db: Session) -> Optional[BackgroundJob]:
        now = datetime.now(timezone.utc)
        # Find queued job whose next_attempt_at <= now, or processing job whose lease expired (crash recovery)
        job = (
            db.query(BackgroundJob)
            .filter(
                or_(
                    BackgroundJob.status == JobStatus.QUEUED,
                    (BackgroundJob.status == JobStatus.PROCESSING) & (BackgroundJob.lease_until < now),
                ),
                BackgroundJob.next_attempt_at <= now,
            )
            .with_for_update(skip_locked=True)
            .first()
        )

        if not job:
            return None

        job.status = JobStatus.PROCESSING
        job.worker_id = self.worker_id
        job.lease_until = now + timedelta(seconds=60)
        db.commit()
        return job

    def execute_job(self, db: Session, job: BackgroundJob):
        try:
            logger.info(f"Worker {self.worker_id} executing {job.job_type.value} [ID: {job.id}]")
            handle_job(db, job)
            job.status = JobStatus.COMPLETED
            job.lease_until = None
            db.commit()
            logger.info(f"Successfully finished job {job.id}")
        except Exception as e:
            db.rollback()
            job.retry_count += 1
            job.last_error = str(e)
            logger.error(f"Error executing job {job.id}: {e}", exc_info=True)

            if job.retry_count >= job.max_retries:
                job.status = JobStatus.FAILED
                job.lease_until = None
            else:
                job.status = JobStatus.QUEUED
                backoff_seconds = (2 ** job.retry_count) * 5
                job.next_attempt_at = datetime.now(timezone.utc) + timedelta(seconds=backoff_seconds)
                job.lease_until = None

            db.commit()

    def run_once(self) -> bool:
        db = SessionLocal()
        try:
            job = self.claim_next_job(db)
            if job:
                self.execute_job(db, job)
                return True
            return False
        finally:
            db.close()

    def start(self):
        self.running = True
        logger.info(f"Background worker engine started [{self.worker_id}]")
        while self.running:
            try:
                processed = self.run_once()
                if not processed:
                    time.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Worker loop exception: {e}")
                time.sleep(self.poll_interval)
