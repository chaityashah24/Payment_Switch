from datetime import datetime, timezone
import enum
from sqlalchemy import Column, String, Integer, DateTime, Enum, Text
from app.database import Base


class JobStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class JobType(str, enum.Enum):
    PROCESS_DELAYED_PAYMENT = "PROCESS_DELAYED_PAYMENT"
    NEFT_BATCH_PROCESS = "NEFT_BATCH_PROCESS"
    SETTLEMENT_PAYOUT_EXECUTE = "SETTLEMENT_PAYOUT_EXECUTE"
    RECONCILIATION_EXECUTE = "RECONCILIATION_EXECUTE"
    REFUND_EXECUTE = "REFUND_EXECUTE"


class BackgroundJob(Base):
    __tablename__ = "background_jobs"

    id = Column(String(36), primary_key=True, index=True)
    job_type = Column(Enum(JobType), nullable=False, index=True)
    payload = Column(Text, nullable=False)  # JSON serialized parameters
    status = Column(Enum(JobStatus), default=JobStatus.QUEUED, nullable=False, index=True)
    
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=5, nullable=False)
    next_attempt_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    lease_until = Column(DateTime(timezone=True), nullable=True)  # Lock lease for crash recovery
    worker_id = Column(String(100), nullable=True)
    
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
