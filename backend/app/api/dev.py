"""Dev-only helpers (shared). Only mounted when MOCK_WHOP=true, so they never exist in production."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.enums import JobType, StateKey
from app.jobs import enqueue
from app.models import CompanyState, Customer, Watch
from app.schemas import OkOut, PaymentEvent

router = APIRouter(prefix="/api/dev", tags=["dev"])


@router.get("/fake-pay/{public_id}")
def fake_pay(public_id: str, db: Session = Depends(get_db)) -> RedirectResponse:
    """Pretend Whop checkout: queues exactly the job a real payment webhook queues."""
    watch = db.scalar(select(Watch).where(Watch.public_id == public_id))
    if watch is None:
        raise HTTPException(404, "watch not found")
    customer = db.get(Customer, watch.customer_id)
    price = db.get(CompanyState, str(StateKey.price_usd))
    event = PaymentEvent(
        whop_payment_id=f"mock-pay-{public_id}",
        whop_user_id=f"mock-user-{customer.id}",
        email=customer.email,
        watch_public_id=public_id,
        amount=float(price.value) if price else settings.starting_price_usd,
    )
    enqueue(db, JobType.payment_received, event.model_dump(mode="json"))
    return RedirectResponse(f"{settings.public_web_url}/watch/{public_id}?paid=1", status_code=302)


@router.post("/run-worker", response_model=OkOut)
def run_worker() -> OkOut:
    """Run every agent once + drain jobs (instead of waiting 15 min)."""
    from app.worker import run_once

    run_once()
    return OkOut(message="ran all agents once")
