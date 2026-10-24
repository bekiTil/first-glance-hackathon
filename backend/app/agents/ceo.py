"""CEO agent. Owner: Yared.

Hourly: read the numbers and what the other agents learned, then set the price, the Growth priorities
and the target events. Price changes go through guardrails ($1-$5, max once an hour) and Natnael's
whop module. Writes an hourly report to the Company Log.
"""

from sqlalchemy import select

from app.agents.base import Agent, AgentContext
from app.config import settings
from app.enums import AgentName, OutboundKind, StateKey
from app.integrations import llm, whop
from app.models import DecisionLog, Job
from app.stats import compute_stats

SYSTEM = (
    "You are the CEO of Ticket Watch, a company run entirely by AI agents. It sells $1-$5 'watches': an "
    "agent checks NYC ticket prices every 15 minutes and alerts the customer when tickets drop under their "
    "max price; refunded if no match. Today is hackathon day: the goal is real paying customers in the next "
    "few hours and a business that can keep growing. Given the numbers and recent agent activity, decide "
    "the price, up to 3 concrete priorities for the Growth agent, and which events to target. Change the "
    "price only with a clear reason from the data. Explain your reasoning in 2-3 sentences."
)
SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["price_usd", "priorities", "target_events", "reasoning"],
    "properties": {
        "price_usd": {"type": "number"},
        "priorities": {"type": "array", "items": {"type": "string"}},
        "target_events": {"type": "array", "items": {"type": "string"}},
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
            f"Numbers: {stats.model_dump_json()}\nCurrent price: ${current_price}\n"
            f"Learned deal weights: {ctx.get_state(StateKey.deal_weights)}\nRecent activity:\n{activity}",
            SCHEMA,
            mock={
                "price_usd": current_price,
                "priorities": [
                    "Knicks fans hunting cheaper November tickets",
                    "Promote the free 'tonight in NYC' page to bring visitors",
                ],
                "target_events": ["Knicks", "Broadway", "concerts at MSG"],
                "reasoning": "Too few sales to judge the price yet; focus Growth on the audience most likely "
                "to buy today.",
            },
        )
        ctx.set_state(StateKey.priorities, decision["priorities"][:3])
        ctx.set_state(StateKey.target_events, decision["target_events"][:5])

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
            target_events=decision["target_events"][:5],
        )
