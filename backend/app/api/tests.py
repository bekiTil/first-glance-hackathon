"""Order a test + read its report. Owner: Bereket (confirm calls Natnael's whop.create_checkout).

TODO(Bereket):
- POST ""  : intake.read_hero(url) (ValueError -> 422 "couldn't read that page") ->
             intake.write_rewrite(original, what_you_do) -> find/create Customer by email ->
             PageTest(kind=customer, status=draft, original, rewrite) -> optional
             solari.screenshot(url, settings.data_dir / f"page-{public_id}.png") ->
             DecisionLog(agent=tester, action="read_page") -> TestOut.
- GET  /{id}: TestOut for PageTest.public_id (never expose the integer id); include
             responses_so_far (count of TestAnswers) and results once delivered. The report page
             polls this every few seconds.
- POST /{id}/confirm: only draft/awaiting_payment -> whop.create_checkout(public_id, email, price)
             where price = company_state["price_usd"] or settings.starting_price_usd ->
             status=awaiting_payment -> CheckoutOut.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import todo
from app.db import get_db
from app.schemas import CheckoutOut, CreateTestRequest, TestOut

router = APIRouter(prefix="/api/tests", tags=["tests"])


@router.post("", response_model=TestOut)
def create_test(body: CreateTestRequest, db: Session = Depends(get_db)) -> TestOut:
    raise todo("Bereket", "create test")


@router.get("/{public_id}", response_model=TestOut)
def get_test(public_id: str, db: Session = Depends(get_db)) -> TestOut:
    raise todo("Bereket", "get test")


@router.post("/{public_id}/confirm", response_model=CheckoutOut)
def confirm_test(public_id: str, db: Session = Depends(get_db)) -> CheckoutOut:
    raise todo("Bereket", "confirm test")
