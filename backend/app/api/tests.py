"""Order a test + read its report. Owner: Bereket (confirm calls Natnael's whop.create_checkout).

- POST ""  : intake.read_hero(url) (ValueError -> 422 "couldn't read that page") ->
             intake.write_rewrite(original, what_you_do) -> find/create Customer by email ->
             PageTest(kind=customer, status=draft, original, rewrite) ->
             DecisionLog(agent=tester, action="read_page") -> TestOut.
- GET  /{id}: TestOut for PageTest.public_id (never the integer id), with responses_so_far and
             results once graded. The report page polls this every few seconds.
- POST /{id}/confirm: only draft/awaiting_payment -> whop.create_checkout(public_id, email, price)
             where price = company_state["price_usd"] or settings.starting_price_usd ->
             status=awaiting_payment -> CheckoutOut.
to_test_out(db, test) is reusable by other routes.
"""

import logging
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.agents import intake
from app.agents.base import AgentContext
from app.db import get_db
from app.enums import AgentName, TestKind, TestStatus
from app.integrations import llm, whop
from app.models import Customer, PageTest, TestAnswer
from app.schemas import CheckoutOut, CreateTestRequest, HeroCopy, TestOut, TestResults
from app.stats import current_price

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tests", tags=["tests"])


def to_test_out(db: Session, test: PageTest) -> TestOut:
    responses = db.scalar(select(func.count(TestAnswer.id)).where(TestAnswer.test_id == test.id)) or 0
    return TestOut(
        id=test.public_id,
        status=test.status,
        url=test.url,
        what_you_do=test.what_you_do,
        original=HeroCopy.model_validate(test.original) if test.original else None,
        rewrite=HeroCopy.model_validate(test.rewrite) if test.rewrite else None,
        price_usd=test.price_paid if test.price_paid is not None else current_price(db),
        responses_so_far=int(responses),
        results=TestResults.model_validate(test.results) if test.results else None,
        created_at=test.created_at,
    )


def _get(db: Session, public_id: str) -> PageTest:
    test = db.scalar(
        select(PageTest).where(PageTest.public_id == public_id, PageTest.kind == TestKind.customer)
    )
    if test is None:
        raise HTTPException(404, "test not found")
    return test


@router.post("", response_model=TestOut)
def create_test(body: CreateTestRequest, db: Session = Depends(get_db)) -> TestOut:
    try:
        url = intake.normalize_url(body.url)
        original = intake.read_hero(url)
    except ValueError as e:
        raise HTTPException(422, "couldn't read that page") from e
    try:
        rewrite = intake.write_rewrite(original, body.what_you_do)
    except llm.LLMError as e:
        log.warning("rewrite failed: %s", e)
        raise HTTPException(503, "Our writer is busy right now. Please try again in a minute.") from e

    customer = db.scalar(
        select(Customer).where(func.lower(Customer.email) == body.email.lower()).order_by(Customer.id)
    )
    if customer is None:
        customer = Customer(email=body.email)
        db.add(customer)
        db.flush()

    test = PageTest(
        kind=TestKind.customer,
        customer_id=customer.id,
        url=url,
        what_you_do=body.what_you_do.strip(),
        original=original.model_dump(),
        rewrite=rewrite.model_dump(),
        status=TestStatus.draft,
    )
    db.add(test)
    db.flush()
    # The Solari screenshot is taken by the Tester at launch, so the founder isn't kept waiting here.

    AgentContext(db=db, agent=AgentName.tester).log(
        "read_page",
        f'Read {urlsplit(url).hostname}: "{original.headline}". Wrote a clearer version: "{rewrite.headline}".',
        test_id=test.public_id,
        site=urlsplit(url).hostname,
        original=original.headline,
        rewrite=rewrite.headline,
    )
    return to_test_out(db, test)


@router.get("/{public_id}", response_model=TestOut)
def get_test(public_id: str, db: Session = Depends(get_db)) -> TestOut:
    return to_test_out(db, _get(db, public_id))


@router.post("/{public_id}/confirm", response_model=CheckoutOut)
def confirm_test(public_id: str, db: Session = Depends(get_db)) -> CheckoutOut:
    test = _get(db, public_id)
    if test.status not in (TestStatus.draft, TestStatus.awaiting_payment):
        raise HTTPException(409, f"this test is already {test.status}")
    customer = db.get(Customer, test.customer_id)
    url = whop.create_checkout(test.public_id, customer.email, current_price(db))
    test.status = TestStatus.awaiting_payment
    return CheckoutOut(checkout_url=url)
