"""Research agent = FirstGlance on ourselves (the hackathon's Terac before/after). Owner: Yared.

Hourly (and when triggered): if we haven't tested our own landing page yet, create a kind=self test:
original = our current landing copy, rewrite = Claude's clearer version. The Tester agent runs it like any
customer test (same Terac study, same /t/:id page). When it's delivered, adopt the winner as our landing
copy (the site switches by itself) and log the before/after. At most MAX_ROUNDS self-tests, so credits
aren't burned every hour.
"""

from sqlalchemy import select

from app.agents.base import Agent, AgentContext
from app.config import settings
from app.enums import AgentName, JobType, StateKey, TestKind, TestStatus, Winner
from app.integrations import llm
from app.jobs import enqueue
from app.models import DecisionLog, Job, PageTest
from app.schemas import HeroCopy, TestResults

DEFAULT_LANDING = HeroCopy(
    headline="Do people get your startup in 5 seconds?",
    subhead="Real people see your landing page for 5 seconds. AI rewrites what confused them, and you get "
    "proof the new version works.",
    cta="Test my page for $15",
)
OUR_PITCH = (
    "FirstGlance shows a startup's landing page to real people for 5 seconds, rewrites what confused them, "
    "and proves which version people understand."
)
MAX_ROUNDS = 2

REWRITE_SYSTEM = (
    "You rewrite the top of a landing page so a stranger understands it in 5 seconds: say WHAT it is and "
    "FOR WHOM in plain words, keep the tone, no hype, no invented claims, similar length. "
    "The button text should say what happens when you click."
)
REWRITE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["headline", "subhead", "cta"],
    "properties": {
        "headline": {"type": "string"},
        "subhead": {"type": "string"},
        "cta": {"type": "string"},
    },
}


def current_landing(ctx: AgentContext) -> HeroCopy:
    stored = ctx.get_state(StateKey.landing_copy)
    return HeroCopy.model_validate(stored) if stored else DEFAULT_LANDING


class ResearchAgent(Agent):
    name = AgentName.research
    every_minutes = 60

    def run(self, ctx: AgentContext, job: Job | None = None) -> None:
        tests = list(
            ctx.db.scalars(select(PageTest).where(PageTest.kind == TestKind.self).order_by(PageTest.id))
        )
        latest = tests[-1] if tests else None

        if latest and latest.status == TestStatus.delivered and not self._adopted(ctx, latest):
            self._adopt(ctx, latest)
            return
        if latest and latest.status not in (TestStatus.delivered, TestStatus.failed):
            return  # still being tested by the Tester agent
        if len(tests) >= MAX_ROUNDS:
            return
        self._start(ctx, round_=len(tests) + 1)

    def _start(self, ctx: AgentContext, round_: int) -> None:
        original = current_landing(ctx)
        rewrite = llm.ask_json(
            REWRITE_SYSTEM,
            f"What the company does: {OUR_PITCH}\nCurrent copy: {original.model_dump_json()}",
            REWRITE_SCHEMA,
            mock={
                "headline": "See if strangers understand your startup in 5 seconds",
                "subhead": "10 real people look at your landing page for 5 seconds and tell you what they think "
                "you do. We rewrite it and prove which version works.",
                "cta": "Test my landing page ($15)",
            },
        )
        test = PageTest(
            kind=TestKind.self,
            url=settings.public_web_url,
            what_you_do=OUR_PITCH,
            original=original.model_dump(),
            rewrite=HeroCopy(**rewrite).model_dump(),
            status=TestStatus.paid,  # we pay with Terac credits; the Tester launches it like any paid test
        )
        ctx.db.add(test)
        ctx.db.flush()
        enqueue(ctx.db, JobType.run_test, {"test_id": test.public_id})
        ctx.log(
            "started_self_test",
            f"Round {round_}: asking real people whether they understand our own landing page in 5 seconds, "
            "current copy vs. a clearer rewrite.",
            test=test.public_id,
            round=round_,
            original=original.headline,
            rewrite=rewrite["headline"],
        )

    def _adopted(self, ctx: AgentContext, test: PageTest) -> bool:
        return any(
            (d.data or {}).get("test") == test.public_id
            for d in ctx.db.scalars(
                select(DecisionLog).where(
                    DecisionLog.agent == AgentName.research, DecisionLog.action == "before_after"
                )
            )
        )

    def _adopt(self, ctx: AgentContext, test: PageTest) -> None:
        results = TestResults.model_validate(test.results)
        o, r = results.original, results.rewrite
        adopted = results.winner == Winner.rewrite
        if adopted:
            ctx.set_state(StateKey.landing_copy, test.rewrite)
        ctx.log(
            "before_after",
            f"Real people who saw our old landing page for 5 seconds: {o.understood}/{o.responses} understood "
            f"what we do (would sign up {o.avg_signup}/5). With the rewrite: {r.understood}/{r.responses} "
            f"({r.avg_signup}/5). "
            + ("Switched the site to the rewrite." if adopted else "Kept the old copy."),
            test=test.public_id,
            understood_before=o.understood_rate,
            understood_after=r.understood_rate,
            signup_before=o.avg_signup,
            signup_after=r.avg_signup,
            adopted=adopted,
        )
