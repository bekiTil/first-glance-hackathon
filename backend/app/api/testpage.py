"""The page Terac participants see (/t/:id) + our landing copy + our own before/after. Owner: Yared."""

import hashlib

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.agents.research import DEFAULT_LANDING
from app.config import settings
from app.db import get_db
from app.db_time import new_public_id
from app.enums import Arm, StateKey, TestKind, TestStatus
from app.models import CompanyState, PageTest, TestAnswer
from app.schemas import HeroCopy, OkOut, SelfTestOut, TestAnswerIn, TestPageOut, TestResults

router = APIRouter(prefix="/api", tags=["test page"])

OPEN_STATUSES = (TestStatus.paid, TestStatus.testing)  # paid: Terac can send people as soon as it launches
CLOSED = "This test has finished. Thank you! You can go back to Terac."


def _test(db: Session, public_id: str) -> PageTest:
    test = db.scalar(select(PageTest).where(PageTest.public_id == public_id))
    if test is None:
        raise HTTPException(404, "test not found")
    return test


def _pick_arm(db: Session, test: PageTest, participant: str | None) -> Arm:
    if participant:
        answered = db.scalar(
            select(TestAnswer.arm).where(
                TestAnswer.test_id == test.id, TestAnswer.participant_ref == participant
            )
        )
        if answered:
            return Arm(answered)
    counts = dict(
        db.execute(
            select(TestAnswer.arm, func.count(TestAnswer.id))
            .where(TestAnswer.test_id == test.id)
            .group_by(TestAnswer.arm)
        ).all()
    )
    original, rewrite = counts.get(Arm.original, 0), counts.get(Arm.rewrite, 0)
    if original != rewrite:
        return Arm.original if original < rewrite else Arm.rewrite
    seed = participant or new_public_id()
    return Arm.original if int(hashlib.sha256(seed.encode()).hexdigest(), 16) % 2 == 0 else Arm.rewrite


@router.get("/t/{public_id}", response_model=TestPageOut)
def get_test_page(
    public_id: str, participant: str | None = None, db: Session = Depends(get_db)
) -> TestPageOut:
    test = _test(db, public_id)
    if test.status not in OPEN_STATUSES or not test.original or not test.rewrite:
        raise HTTPException(409, CLOSED)
    arm = _pick_arm(db, test, participant)
    hero = test.original if arm == Arm.original else test.rewrite
    return TestPageOut(
        id=public_id, arm=arm, hero=HeroCopy.model_validate(hero), seconds=settings.test_seconds
    )


@router.post("/t/{public_id}/answers", response_model=OkOut)
def submit_answer(public_id: str, body: TestAnswerIn, db: Session = Depends(get_db)) -> OkOut:
    test = _test(db, public_id)
    if test.status not in OPEN_STATUSES:
        return OkOut(ok=False, message=CLOSED)
    answer = TestAnswer(
        test_id=test.id,
        participant_ref=body.participant_ref or f"anon-{new_public_id()}",
        arm=body.arm,
        answer=body.answer.strip()[:1000],
        signup=body.signup,
    )
    try:
        with db.begin_nested():
            db.add(answer)
    except IntegrityError:
        return OkOut(message="Already received. Thank you! Go back to Terac and mark the task complete.")
    return OkOut(message="Thanks! Go back to Terac and mark the task complete.")


@router.get("/landing-copy", response_model=HeroCopy)
def landing_copy(db: Session = Depends(get_db)) -> HeroCopy:
    row = db.get(CompanyState, str(StateKey.landing_copy))
    return HeroCopy.model_validate(row.value) if row and row.value else DEFAULT_LANDING


@router.get("/self-test", response_model=SelfTestOut)
def self_test(db: Session = Depends(get_db)) -> SelfTestOut:
    test = db.scalar(select(PageTest).where(PageTest.kind == TestKind.self).order_by(PageTest.id.desc()))
    if test is None:
        return SelfTestOut()
    return SelfTestOut(
        status=test.status,
        original=HeroCopy.model_validate(test.original) if test.original else None,
        rewrite=HeroCopy.model_validate(test.rewrite) if test.rewrite else None,
        results=TestResults.model_validate(test.results) if test.results else None,
    )
