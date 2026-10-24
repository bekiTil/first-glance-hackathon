"""Enqueue work for the agents service. API routes call this; they never run agents directly."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.enums import JobType
from app.models import Job


def enqueue(
    db: Session, job_type: JobType, payload: dict | None = None, run_after: datetime | None = None
) -> Job:
    job = Job(type=job_type, payload=payload or {})
    if run_after:
        job.run_after = run_after
    db.add(job)
    db.flush()
    return job
