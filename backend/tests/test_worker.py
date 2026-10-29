import uuid
import json
from app.models.job import BackgroundJob, JobType, JobStatus
from app.worker.engine import WorkerEngine


def test_worker_claiming_and_execution(db):
    job = BackgroundJob(
        id=str(uuid.uuid4()),
        job_type=JobType.PROCESS_DELAYED_PAYMENT,
        payload=json.dumps({"payment_id": "non_existent_demo_id"}),
        status=JobStatus.QUEUED,
    )
    db.add(job)
    db.commit()

    worker = WorkerEngine(worker_id="test-worker-01")
    claimed = worker.claim_next_job(db)
    assert claimed is not None
    assert claimed.id == job.id
    assert claimed.status == JobStatus.PROCESSING
    assert claimed.worker_id == "test-worker-01"

    # Execute
    worker.execute_job(db, claimed)
    assert claimed.status == JobStatus.COMPLETED
