"""Growth agent. Owner: Yared.

TODO(Yared): implement run(). Spec:
- Every 30 min. Read ctx.get_state(StateKey.priorities) (written by the CEO).
- Research with exa.search(...); write ONE honest marketing action with llm.ask_text (post, outreach,
  event-specific page, or ad draft). Say it's AI-run; never claim we buy tickets.
- Only publish if ctx.check(OutboundKind.post | OutboundKind.ad, content, ...) allows.
  Ads go through whop.create_ad_draft(...) (Natnael's module, his money) with budget_usd in meta.
- ctx.log(...) what was published, where, and why (link if there is one).
"""

from app.agents.base import Agent, AgentContext
from app.enums import AgentName
from app.models import Job


class GrowthAgent(Agent):
    name = AgentName.growth
    every_minutes = 30

    def run(self, ctx: AgentContext, job: Job | None = None) -> None:
        raise NotImplementedError("TODO(Yared): growth")
