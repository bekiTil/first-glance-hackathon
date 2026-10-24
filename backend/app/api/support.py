"""Contact form -> Support agent. Owner: Natnael.

TODO(Natnael): enqueue(db, JobType.support_message, body.model_dump(mode="json")) ->
OkOut("Got it, we'll email you shortly.").
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import todo
from app.db import get_db
from app.schemas import OkOut, SupportRequest

router = APIRouter(prefix="/api/support", tags=["support"])


@router.post("", response_model=OkOut)
def contact(body: SupportRequest, db: Session = Depends(get_db)) -> OkOut:
    raise todo("Natnael", "contact form")
