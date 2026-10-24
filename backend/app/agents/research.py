"""Research agent (human-in-the-loop via Terac). Owner: Yared.

TODO(Yared): implement run(). Spec:
- Hourly. Decides on its own when it needs real people:
  1. No deal_preferences Study yet -> terac.request_quote(...) + terac.launch(...), save a Study row
     (round=1), ctx.log("launched_study", why).
  2. Study running -> terac.get_submissions(...); when answers are in, turn them into weights in the
     deal_score.DEFAULT_WEIGHTS format and ctx.set_state(StateKey.deal_weights, weights).
  3. After weights change -> launch round 2 to measure the improvement (the required before/after).
  Also a landing_page study ("would you pay $3? what's unclear?").
- If Terac only works through the MCP (browser login), run the studies from Claude Code and write the
  same Study rows + deal_weights instead.
"""

from app.agents.base import Agent, AgentContext
from app.enums import AgentName
from app.models import Job


class ResearchAgent(Agent):
    name = AgentName.research
    every_minutes = 60

    def run(self, ctx: AgentContext, job: Job | None = None) -> None:
        raise NotImplementedError("TODO(Yared): research")
