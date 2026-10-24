"""Finance agent. Owner: Natnael (the only person who handles money).

TODO(Natnael): implement run(). Spec:
- job payment_received (payload = schemas.PaymentEvent): ignore duplicates (same whop_payment_id);
  find the Watch by watch_public_id; save a Payment row; Watch.status=active, Watch.price_paid=amount;
  store whop_user_id on the Customer. ctx.log("payment_recorded", ...).
- hourly (job is None): for active watches whose events have ALL passed:
    an Alert was ever sent -> Watch.status=expired, no refund
    no Alert ever sent     -> if ctx.check(OutboundKind.refund, amount=..., amount_paid=...):
                              whop.refund(...), Payment.status=refunded, Watch.status=refunded
  Our own records decide refunds, never what the customer says.
"""

from app.agents.base import Agent, AgentContext
from app.enums import AgentName, JobType
from app.models import Job


class FinanceAgent(Agent):
    name = AgentName.finance
    every_minutes = 60
    handles = (JobType.payment_received,)

    def run(self, ctx: AgentContext, job: Job | None = None) -> None:
        raise NotImplementedError("TODO(Natnael): finance")
