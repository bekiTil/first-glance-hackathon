"""Inbound Whop payment webhook. Owner: Natnael.

Rule: routes only enqueue jobs (app.jobs.enqueue); the Finance agent does the work.
- POST /whop: verify + normalize the Whop event (bad signature -> 400), queue payment_received.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.enums import JobType
from app.integrations import whop
from app.jobs import enqueue
from app.schemas import OkOut

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/whop", response_model=OkOut)
async def whop_webhook(request: Request, db: Session = Depends(get_db)) -> OkOut:
    body = await request.body()
    try:
        event = whop.parse_webhook(body, dict(request.headers))
    except ValueError as e:
        raise HTTPException(400, f"invalid webhook: {e}") from e
    if event is None:
        return OkOut(message="ignored")
    enqueue(db, JobType.payment_received, event.model_dump(mode="json"))
    return OkOut(message="queued")
