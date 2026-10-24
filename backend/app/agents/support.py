"""Sales & support agent. Owner: Natnael.

TODO(Natnael): implement run(). Spec:
- Consumes support_message jobs (payload = schemas.SupportRequest from the contact form).
- Answer with llm.ask_text: what FirstGlance is ($15, ~10 real people see your page for 5 seconds,
  AI rewrite tested against yours, refund if ours doesn't win), how long it takes, where their
  report is ({PUBLIC_WEB_URL}/report/<test_id> if given). Never promise things we don't do.
- Send with notify.send_email only if ctx.check(OutboundKind.email, answer) allows.
- Refund requests: explain the automatic guarantee; never refund here (Finance decides from records).
- ctx.log("answered_customer", ...) without the customer's email in data.
"""

from app.agents.base import Agent, AgentContext
from app.enums import AgentName, JobType
from app.models import Job


class SupportAgent(Agent):
    name = AgentName.support
    handles = (JobType.support_message,)

    def run(self, ctx: AgentContext, job: Job | None = None) -> None:
        raise NotImplementedError("TODO(Natnael): support")
