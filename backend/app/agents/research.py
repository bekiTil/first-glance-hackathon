"""Research agent (human-in-the-loop via Terac). Owner: Yared.

Runs hourly (and can be triggered with a run_agent job). It decides on its own when it needs people:
  round 1: no study yet            -> create + launch a Terac study (our /study/<id> page)
  round 1 has enough answers       -> fit deal weights from what people picked, rewrite the landing
                                      copy from what confused them, launch round 2 on NEW ticket sets
  round 2 has enough answers       -> measure before/after on the held-out round-2 picks:
                                      "cheapest wins" (v1) vs. learned weights (v2), and landing
                                      willingness-to-pay v1 copy vs. v2 copy
Every step is logged to the Company Log. With MOCK_TERAC=true, simulated people answer.
"""

import random

from sqlalchemy import func, select

from app.agents.base import Agent, AgentContext
from app.agents.study_design import DEFAULT_LANDING, ROUNDS, V1_WEIGHTS, agreement, fit_weights
from app.config import settings
from app.db_time import new_public_id, utcnow
from app.enums import AgentName, StateKey, StudyKind, StudyStatus
from app.integrations import llm, terac
from app.models import Job, Study, StudyAnswer
from app.schemas import LandingCopy

ENOUGH_ANSWERS = max(5, int(settings.terac_participants * 0.8))  # don't wait forever for stragglers

COPY_SYSTEM = (
    "You improve the landing page of Ticket Watch, an AI-run service that watches NYC ticket prices for "
    "$3 and alerts by email/text when tickets drop under the customer's max price (refund if no match; "
    "it never buys tickets). Rewrite the copy to fix what real people said was unclear. Honest, concrete, short."
)
COPY_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["headline", "subhead", "bullets"],
    "properties": {
        "headline": {"type": "string"},
        "subhead": {"type": "string"},
        "bullets": {"type": "array", "items": {"type": "string"}},
    },
}


def landing_copy(ctx: AgentContext) -> LandingCopy:
    stored = ctx.get_state(StateKey.landing_copy)
    return LandingCopy.model_validate(stored) if stored else DEFAULT_LANDING


class ResearchAgent(Agent):
    name = AgentName.research
    every_minutes = 60

    def run(self, ctx: AgentContext, job: Job | None = None) -> None:
        studies = {
            s.round: s for s in ctx.db.scalars(select(Study).where(Study.kind == StudyKind.deal_preferences))
        }
        if 1 not in studies:
            self._launch(
                ctx, round_=1, why="No data yet on what people consider a good deal; asking real people."
            )
            return
        first = studies[1]
        if first.status in (StudyStatus.waiting_for_public_url, StudyStatus.quoted):
            self._retry_launch(ctx, first)
            return
        if first.status == StudyStatus.running and self._ready(ctx, first):
            self._learn_from_round_1(ctx, first)
            self._launch(
                ctx, round_=2, why="Weights and copy changed; testing on new ticket sets to measure it."
            )
            return
        second = studies.get(2)
        if second is None:
            return
        if second.status in (StudyStatus.waiting_for_public_url, StudyStatus.quoted):
            self._retry_launch(ctx, second)
        elif second.status == StudyStatus.running and self._ready(ctx, second):
            self._measure(ctx, first, second)

    # ---------- steps ----------

    def _launch(self, ctx: AgentContext, round_: int, why: str) -> None:
        study = Study(
            kind=StudyKind.deal_preferences,
            round=round_,
            status=StudyStatus.quoted,
            request={"public_id": new_public_id(), "landing": landing_copy(ctx).model_dump()},
        )
        ctx.db.add(study)
        ctx.db.flush()
        self._retry_launch(ctx, study, why=why)

    def _retry_launch(self, ctx: AgentContext, study: Study, why: str = "") -> None:
        task_url = f"{settings.public_web_url.rstrip('/')}/study/{study.request['public_id']}"
        if not settings.mock_terac and not task_url.startswith("https://"):
            if study.status != StudyStatus.waiting_for_public_url:
                study.status = StudyStatus.waiting_for_public_url
                ctx.log(
                    "study_waiting",
                    "Terac participants need a public https study page; "
                    "waiting for the site to be deployed (PUBLIC_WEB_URL).",
                    round=study.round,
                )
            return
        quote = terac.create_study(
            title="Which concert/game tickets would you buy? (5 min)",
            description="Compare 5 sets of 3 ticket listings and pick the one you'd buy, then rate a short "
            "description of a ticket price-alert service. About 5 minutes.",
            task_url=task_url,
            participants=settings.terac_participants,
            minutes=5,
        )
        if quote.get("affordable") is False:
            study.status = StudyStatus.quoted
            study.request = {**study.request, "quote": quote}
            ctx.log(
                "study_unaffordable", "Terac balance doesn't cover the study; waiting for credits.", **quote
            )
            return
        study.terac_id = quote["id"]
        terac.launch(quote["id"])
        study.status = StudyStatus.running
        study.launched_at = utcnow()
        study.request = {**study.request, "quote": quote, "task_url": task_url}
        ctx.log(
            "launched_study",
            why or f"Launching round {study.round}.",
            round=study.round,
            participants=settings.terac_participants,
            cost_per_person=quote.get("cost_per_participant"),
            total_cost=quote.get("total_cost"),
        )
        if settings.mock_terac:
            _simulate_answers(ctx, study)

    def _ready(self, ctx: AgentContext, study: Study) -> bool:
        count = ctx.db.scalar(select(func.count(StudyAnswer.id)).where(StudyAnswer.study_id == study.id))
        return (count or 0) >= ENOUGH_ANSWERS

    def _learn_from_round_1(self, ctx: AgentContext, study: Study) -> None:
        answers = _answers(ctx, study)
        picks = [(p["set"], p["option"]) for a in answers for p in a.picks]
        weights = fit_weights(ROUNDS[1], picks)
        before = agreement(ROUNDS[1], picks, V1_WEIGHTS)
        fitted = agreement(ROUNDS[1], picks, weights)
        ctx.set_state(StateKey.deal_weights, weights)
        ctx.log(
            "updated_deal_weights",
            f"Real people picked the cheapest ticket only {before:.0%} of the time. Learned weights "
            f"match {fitted:.0%} of their picks; the Watcher now ranks deals this way.",
            weights=weights,
            responses=len(answers),
            agreement_v1=before,
            agreement_fitted=fitted,
        )

        unclear = [a.unclear for a in answers if a.unclear.strip()]
        willingness = _avg([a.willingness for a in answers])
        old = landing_copy(ctx)
        new = llm.ask_json(
            COPY_SYSTEM,
            f"Current copy: {old.model_dump_json()}\nAverage willingness to pay $3 (1-5): {willingness}\n"
            f"What people said was unclear or missing:\n- " + "\n- ".join(unclear[:30]),
            COPY_SCHEMA,
            mock={
                "headline": "Pick your max ticket price. Get a text the moment it drops under it.",
                "subhead": "We check SeatGeek and Ticketmaster every 15 minutes. You buy on the official site; "
                "we never touch your payment.",
                "bullets": [
                    "$3 per watch, refunded if we never find a match",
                    "Email + text alerts",
                    "Run entirely by AI agents",
                ],
            },
        )
        copy = LandingCopy(**new, version=old.version + 1)
        ctx.set_state(StateKey.landing_copy, copy.model_dump())
        study.status = StudyStatus.completed
        study.completed_at = utcnow()
        study.results = {
            "weights": weights,
            "agreement_v1": before,
            "agreement_fitted": fitted,
            "willingness": willingness,
            "responses": len(answers),
        }
        ctx.log(
            "updated_landing_copy",
            f"Rewrote the landing page from {len(unclear)} comments about what was unclear "
            f"(willingness to pay was {willingness}/5).",
            headline=copy.headline,
            version=copy.version,
        )

    def _measure(self, ctx: AgentContext, first: Study, second: Study) -> None:
        answers = _answers(ctx, second)
        picks = [(p["set"], p["option"]) for a in answers for p in a.picks]
        weights = first.results.get("weights", V1_WEIGHTS)
        before = agreement(ROUNDS[2], picks, V1_WEIGHTS)
        after = agreement(ROUNDS[2], picks, weights)
        w_before = first.results.get("willingness")
        w_after = _avg([a.willingness for a in answers])
        second.status = StudyStatus.completed
        second.completed_at = utcnow()
        second.results = {
            "agreement_v1": before,
            "agreement_v2": after,
            "willingness_v1": w_before,
            "willingness_v2": w_after,
            "responses": len(answers),
        }
        ctx.log(
            "before_after",
            f"On new ticket sets, 'cheapest wins' matched real people {before:.0%} of the time; the "
            f"weights learned from people matched {after:.0%}. Willingness to pay went "
            f"{w_before}/5 -> {w_after}/5 after the copy rewrite.",
            **second.results,
        )


def _answers(ctx: AgentContext, study: Study) -> list[StudyAnswer]:
    return list(ctx.db.scalars(select(StudyAnswer).where(StudyAnswer.study_id == study.id)))


def _avg(values: list[int | None]) -> float:
    vals = [v for v in values if v is not None]
    return round(sum(vals) / len(vals), 2) if vals else 0.0


def _simulate_answers(ctx: AgentContext, study: Study) -> None:
    """Mock mode only: fake people who value lower-level seats and weekends a bit."""
    rng = random.Random(study.id * 7919)
    hidden = {"price": 1.0, "lower_level": 0.6, "weekend": 0.25}
    from app.agents.study_design import option_score

    for n in range(settings.terac_participants):
        picks = []
        for i, s in enumerate(ROUNDS[study.round]):
            max_price = max(o.price for o in s.options)
            best = max(s.options, key=lambda o: option_score(o, max_price, hidden) + rng.uniform(0, 0.15))
            picks.append({"set": i, "option": best.label, "why": ""})
        ctx.db.add(
            StudyAnswer(
                study_id=study.id,
                participant_ref=f"mock-{study.round}-{n}",
                picks=picks,
                willingness=rng.choice([2, 3, 3, 4]) + (1 if study.round == 2 and rng.random() < 0.5 else 0),
                unclear=rng.choice(["", "Do you buy the tickets for me?", "Which sites do you check?", ""]),
            )
        )
    ctx.db.flush()
