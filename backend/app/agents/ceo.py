"""CEO agent. Owner: Yared.

TODO(Yared): implement run(). Spec:
- Hourly. Read stats.compute_stats(ctx.db) (and anything else useful), then decide with llm.ask_json:
  price (USD), up to 3 priorities for Growth, target event categories, and the reasoning.
- Write ctx.set_state(StateKey.priorities, [...]) and ctx.set_state(StateKey.target_events, [...]).
- Price change only if ctx.check(OutboundKind.price_change, new_price=...) allows, then
  whop.update_price(new_price) (Natnael's module) and ctx.set_state(StateKey.price_usd, new_price),
  ctx.log("price_changed", reasoning, old=..., new=...).
- Always ctx.log("hourly_report", reasoning, stats=..., priorities=...).
"""

from app.agents.base import Agent, AgentContext
from app.enums import AgentName
from app.models import Job


class CeoAgent(Agent):
    name = AgentName.ceo
    every_minutes = 60

    def run(self, ctx: AgentContext, job: Job | None = None) -> None:
        raise NotImplementedError("TODO(Yared): ceo")
