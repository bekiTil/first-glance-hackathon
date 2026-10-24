"""Study page API (Terac sends participants to {PUBLIC_WEB_URL}/study/<id>). Owner: Yared."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.agents.study_design import DEFAULT_LANDING, ROUNDS
from app.config import settings
from app.db import get_db
from app.db_time import new_public_id
from app.enums import StateKey, StudyStatus
from app.models import CompanyState, Study, StudyAnswer
from app.schemas import LandingCopy, OkOut, StudyAnswerIn, StudyOut

router = APIRouter(prefix="/api/studies", tags=["studies"])


def _price(db: Session) -> float:
    row = db.get(CompanyState, str(StateKey.price_usd))
    return float(row.value) if row else settings.starting_price_usd


def _study(db: Session, public_id: str) -> Study:
    for study in db.scalars(select(Study)):
        if (study.request or {}).get("public_id") == public_id:
            return study
    raise HTTPException(404, "study not found")


@router.get("/landing-copy", response_model=LandingCopy)
def current_landing_copy(db: Session = Depends(get_db)) -> LandingCopy:
    """The landing page reads its copy from here, so the Research agent's rewrite goes live."""
    row = db.get(CompanyState, str(StateKey.landing_copy))
    return LandingCopy.model_validate(row.value) if row else DEFAULT_LANDING


@router.get("/{public_id}", response_model=StudyOut)
def get_study(public_id: str, db: Session = Depends(get_db)) -> StudyOut:
    study = _study(db, public_id)
    landing = study.request.get("landing")
    return StudyOut(
        id=public_id,
        round=study.round,
        sets=ROUNDS[study.round],
        landing=LandingCopy.model_validate(landing) if landing else DEFAULT_LANDING,
        price_usd=_price(db),
    )


@router.post("/{public_id}/answers", response_model=OkOut)
def submit_answers(public_id: str, body: StudyAnswerIn, db: Session = Depends(get_db)) -> OkOut:
    study = _study(db, public_id)
    if study.status == StudyStatus.completed:
        return OkOut(message="This study is closed. Thank you!")
    sets = ROUNDS[study.round]
    for pick in body.picks:
        if not 0 <= pick.set < len(sets) or pick.option not in {o.label for o in sets[pick.set].options}:
            raise HTTPException(422, f"invalid pick {pick}")
    if len({p.set for p in body.picks}) != len(sets):
        raise HTTPException(422, "answer every set")
    answer = StudyAnswer(
        study_id=study.id,
        participant_ref=body.participant_ref or f"anon-{new_public_id()}",
        picks=[p.model_dump() for p in body.picks],
        willingness=body.willingness,
        unclear=body.unclear[:2000],
    )
    try:
        with db.begin_nested():
            db.add(answer)
    except IntegrityError:
        return OkOut(message="Already received. Thank you!")
    return OkOut(message="Thank you! Go back to Terac and mark the task complete.")
