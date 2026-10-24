"""The page Terac participants see (/t/:id) + our landing copy + our own before/after. Owner: Yared.

TODO(Yared):
- GET /api/t/{id}?participant=<teracSubmissionId>: only while status=testing. Give this participant
  ONE arm: the one with fewer answers so far (ties -> random); same participant -> same arm.
  Return TestPageOut(arm, hero=original|rewrite, seconds=settings.test_seconds).
- POST /api/t/{id}/answers: TestAnswerIn -> TestAnswer (dedupe on participant_ref; anonymous ->
  random ref). Reply OkOut("Thanks! Go back to Terac and mark the task complete.").
- GET /api/landing-copy: company_state["landing_copy"] or research.DEFAULT_LANDING (the landing page
  reads its headline from here, so the winning copy goes live automatically).
- GET /api/self-test: latest kind=self PageTest as SelfTestOut (Company Log's before/after card).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import todo
from app.db import get_db
from app.schemas import HeroCopy, OkOut, SelfTestOut, TestAnswerIn, TestPageOut

router = APIRouter(prefix="/api", tags=["test page"])


@router.get("/t/{public_id}", response_model=TestPageOut)
def get_test_page(
    public_id: str, participant: str | None = None, db: Session = Depends(get_db)
) -> TestPageOut:
    raise todo("Yared", "test page")


@router.post("/t/{public_id}/answers", response_model=OkOut)
def submit_answer(public_id: str, body: TestAnswerIn, db: Session = Depends(get_db)) -> OkOut:
    raise todo("Yared", "submit answer")


@router.get("/landing-copy", response_model=HeroCopy)
def landing_copy(db: Session = Depends(get_db)) -> HeroCopy:
    raise todo("Yared", "landing copy")


@router.get("/self-test", response_model=SelfTestOut)
def self_test(db: Session = Depends(get_db)) -> SelfTestOut:
    raise todo("Yared", "self test")
