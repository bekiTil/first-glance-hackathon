"""Finance agent. Owner: Natnael (the only person who handles money).

TODO(Natnael): implement run(). Spec:
- job payment_received (payload = schemas.PaymentEvent): ignore duplicates (same whop_payment_id);
  find the PageTest by test_public_id; save a Payment row; PageTest.status=paid, price_paid=amount;
  store whop_user_id on the Customer; enqueue(ctx.db, JobType.run_test, {"test_id": public_id})
  so the Tester starts right away. ctx.log("payment_recorded", ...).
- every 10 min (job is None): the money-back guarantee, decided from our own records only:
    delivered customer tests whose results.winner != "rewrite"  -> refund
    tests stuck in paid/testing/failed for > 3 hours             -> refund
  For each: if ctx.check(OutboundKind.refund, amount=..., amount_paid=...): whop.refund(...),
  Payment.status=refunded, PageTest.status=refunded, email the customer, ctx.log("refunded", why).
"""

from app.agents.base import Agent, AgentContext
from app.enums import AgentName, JobType
from app.models import Job


class FinanceAgent(Agent):
    name = AgentName.finance
    every_minutes = 10
    handles = (JobType.payment_received,)

    def run(self, ctx: AgentContext, job: Job | None = None) -> None:
        raise NotImplementedError("TODO(Natnael): finance")
