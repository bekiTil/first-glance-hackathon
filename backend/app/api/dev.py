"""Dev-only helpers (shared). Only mounted when MOCK_WHOP=true, so they never exist in production."""

import random

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.enums import Arm, JobType, StateKey
from app.jobs import enqueue
from app.models import CompanyState, Customer, PageTest, TestAnswer
from app.schemas import OkOut, PaymentEvent

router = APIRouter(prefix="/api/dev", tags=["dev"])


def _test(db: Session, public_id: str) -> PageTest:
    test = db.scalar(select(PageTest).where(PageTest.public_id == public_id))
    if test is None:
        raise HTTPException(404, "test not found")
    return test


@router.get("/fake-pay/{public_id}")
def fake_pay(public_id: str, db: Session = Depends(get_db)) -> RedirectResponse:
    """Pretend Whop checkout: queues exactly the job a real payment webhook queues."""
    test = _test(db, public_id)
    customer = db.get(Customer, test.customer_id) if test.customer_id else None
    price = db.get(CompanyState, str(StateKey.price_usd))
    event = PaymentEvent(
        whop_payment_id=f"mock-pay-{public_id}",
        whop_user_id=f"mock-user-{customer.id}" if customer else None,
        email=customer.email if customer else None,
        test_public_id=public_id,
        amount=float(price.value) if price else settings.starting_price_usd,
    )
    enqueue(db, JobType.payment_received, event.model_dump(mode="json"))
    return RedirectResponse(f"{settings.public_web_url}/report/{public_id}?paid=1", status_code=302)


@router.post("/fake-answers/{public_id}", response_model=OkOut)
def fake_answers(public_id: str, n: int = 10, db: Session = Depends(get_db)) -> OkOut:
    """Pretend Terac participants answered (rewrite is understood more often), so grading can be tested."""
    test = _test(db, public_id)
    for i in range(n):
        arm = Arm.original if i % 2 == 0 else Arm.rewrite
        gets_it = random.random() < (0.4 if arm == Arm.original else 0.85)
        db.add(
            TestAnswer(
                test_id=test.id,
                participant_ref=f"fake-{public_id}-{i}",
                arm=arm,
                signup=random.randint(2, 5),
                answer=test.what_you_do
                if gets_it
                else random.choice(["no idea", "some AI thing?", "a newsletter"]),
            )
        )
    return OkOut(message=f"added {n} fake answers")


@router.post("/run-worker", response_model=OkOut)
def run_worker() -> OkOut:
    """Run every agent once + drain jobs (instead of waiting for the schedule)."""
    from app.worker import run_once

    run_once()
    return OkOut(message="ran all agents once")
