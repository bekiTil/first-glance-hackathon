"""Inbound Whop payment webhook. Owner: Natnael.

Rule: routes only enqueue jobs (app.jobs.enqueue); the Finance agent does the work.
TODO(Natnael):
- POST /whop: whop.parse_webhook(body, headers) -> PaymentEvent | None (ValueError = bad signature
  -> 400) -> enqueue(db, JobType.payment_received, event.model_dump(mode="json")) -> OkOut.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api import todo
from app.db import get_db
from app.schemas import OkOut

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/whop", response_model=OkOut)
async def whop_webhook(request: Request, db: Session = Depends(get_db)) -> OkOut:
    raise todo("Natnael", "Whop webhook")
