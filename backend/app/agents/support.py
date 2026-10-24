"""Sales & support agent. Owner: Natnael.

TODO(Natnael): implement run(). Spec:
- Consumes jobs: email_reply (payload ReplyIn with alert_id + action) and sms_received (ReplyIn with
  phone + text). Texts "1"/"2"/"3" map to ReplyAction bought/keep/reject.
- bought: Alert.status=bought, Watch.status=purchased, Outcome(bought=True). keep: Outcome(bought=False).
  reject: Alert.status=rejected, Outcome with a RejectReason; judge it against the saved alert.listing
  + screenshot ("higher at checkout" / "sold out within ~15 min" = not a match; a new wish = still a match).
- "STOP" -> customer.sms_consent=False. Any other text -> answer with llm.ask_text and reply by
  notify.send_sms, only if ctx.check(OutboundKind.sms, ...) allows.
- Never refund here: refunds are decided only by the Finance agent from our own records.
- ctx.log(...) every decision (no emails/phone numbers in the data).
"""

from app.agents.base import Agent, AgentContext
from app.enums import AgentName, JobType
from app.models import Job


class SupportAgent(Agent):
    name = AgentName.support
    handles = (JobType.email_reply, JobType.sms_received)

    def run(self, ctx: AgentContext, job: Job | None = None) -> None:
        raise NotImplementedError("TODO(Natnael): support")
