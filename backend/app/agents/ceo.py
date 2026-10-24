"""CEO agent. Owner: Yared.

Hourly: read the numbers and recent agent activity, then set the price, the Growth priorities and the
target audiences. Price changes go through guardrails ($5-$30, max once an hour) and Natnael's whop
module. Writes an hourly report to the Company Log.
"""

from sqlalchemy import select

from app.agents.base import Agent, AgentContext
from app.config import settings
from app.enums import AgentName, OutboundKind, StateKey
from app.integrations import llm, whop
from app.models import DecisionLog, Job
from app.stats import compute_stats

SYSTEM = (
    "You are the CEO of FirstGlance, a company run entirely by AI agents. For $5-$30 per test, ~10 real "
    "people see a startup's landing page for 5 seconds and say what they think it does; an AI rewrite is "
    "tested against the original and the customer gets proof of which works (refund if ours doesn't win). "
    "Today is hackathon day: the goal is real paying customers in the next few hours and a business that "
    "can keep growing. Given the numbers and recent agent activity, decide the price, up to 3 concrete "
    "priorities for the Growth agent, and which audiences to target. Change the price only with a clear "
    "reason from the data. Explain your reasoning in 2-3 sentences."
)
SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["price_usd", "priorities", "target_audiences", "reasoning"],
    "properties": {
        "price_usd": {"type": "number"},
        "priorities": {"type": "array", "items": {"type": "string"}},
        "target_audiences": {"type": "array", "items": {"type": "string"}},
        "reasoning": {"type": "string"},
    },
}


class CeoAgent(Agent):
    name = AgentName.ceo
    every_minutes = 60

    def run(self, ctx: AgentContext, job: Job | None = None) -> None:
        stats = compute_stats(ctx.db)
        current_price = float(ctx.get_state(StateKey.price_usd, settings.starting_price_usd))
        recent = ctx.db.scalars(select(DecisionLog).order_by(DecisionLog.id.desc()).limit(25)).all()
        activity = "\n".join(f"- [{d.agent}] {d.action}: {d.reason[:160]}" for d in reversed(recent))
        decision = llm.ask_json(
            SYSTEM,
            f"Numbers: {stats.model_dump_json()}\nCurrent price: ${current_price}\nRecent activity:\n{activity}",
            SCHEMA,
            mock={
                "price_usd": current_price,
                "priorities": [
                    "Hackathon teams polishing landing pages before the 6:45pm deadline",
                    "Indie founders launching on Product Hunt this week",
                ],
                "target_audiences": ["hackathon teams", "indie founders", "early-stage startups"],
                "reasoning": "Too few sales to judge the price yet; focus Growth on founders who need a "
                "clearer page today.",
            },
        )
        ctx.set_state(StateKey.priorities, decision["priorities"][:3])
        ctx.set_state(StateKey.target_audiences, decision["target_audiences"][:5])

        new_price = round(float(decision["price_usd"]), 2)
        if new_price != current_price and ctx.check(OutboundKind.price_change, new_price=new_price):
            if whop.update_price(new_price):
                ctx.set_state(StateKey.price_usd, new_price)
                ctx.log("price_changed", decision["reasoning"], old=current_price, new=new_price)

        ctx.log(
            "hourly_report",
            decision["reasoning"],
            stats=stats.model_dump(),
            priorities=decision["priorities"][:3],
            target_audiences=decision["target_audiences"][:5],
        )
