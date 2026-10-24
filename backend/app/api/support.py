"""Contact form -> Support agent. Owner: Natnael.

Queues a support_message job; the Support agent answers by email.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.enums import JobType
from app.jobs import enqueue
from app.schemas import OkOut, SupportRequest

router = APIRouter(prefix="/api/support", tags=["support"])


@router.post("", response_model=OkOut)
def contact(body: SupportRequest, db: Session = Depends(get_db)) -> OkOut:
    enqueue(db, JobType.support_message, body.model_dump(mode="json"))
    return OkOut(message="Got it, we'll email you shortly.")
