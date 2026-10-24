"""Research agent = FirstGlance on ourselves (the hackathon's Terac before/after). Owner: Yared.

TODO(Yared): implement run(). Spec:
- Hourly. If there's no kind=self PageTest yet: create one for OUR landing page:
  original = current landing copy (company_state["landing_copy"] or DEFAULT_LANDING),
  rewrite = Claude's clearer version, what_you_do = our one-sentence pitch, status=paid.
  The Tester agent runs it exactly like a customer test (same Terac flow, same /t/:id page).
- When it's delivered: if the rewrite won, set company_state["landing_copy"] to it (the site
  switches automatically) and ctx.log("before_after", "X/5 understood v1, Y/5 understood v2 ...").
  Optionally a second round on the new copy.
"""

from app.agents.base import Agent, AgentContext
from app.enums import AgentName
from app.models import Job
from app.schemas import HeroCopy

DEFAULT_LANDING = HeroCopy(
    headline="Do people get your startup in 5 seconds?",
    subhead="Real people see your landing page for 5 seconds. AI rewrites what confused them, and you get "
    "proof the new version works.",
    cta="Test my page for $15",
)
OUR_PITCH = (
    "FirstGlance tests whether strangers understand a startup's landing page in 5 seconds and rewrites it."
)


class ResearchAgent(Agent):
    name = AgentName.research
    every_minutes = 60

    def run(self, ctx: AgentContext, job: Job | None = None) -> None:
        raise NotImplementedError("TODO(Yared): research")
