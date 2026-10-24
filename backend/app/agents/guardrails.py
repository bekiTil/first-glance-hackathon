"""Compliance agent = hard limits in code, checked before anything leaves the company.
Owner: Bereket.

SHARED contract: every agent calls ctx.check(OutboundKind.<kind>, content, **meta) before sending an
email, text, post or ad, changing the price, or refunding, and sends nothing unless the verdict is allowed.
meta keys by kind:
  sms:          sms_consent=bool, phone_verified=bool
  price_change: new_price=float
  ad:           budget_usd=float
  refund:       amount=float, amount_paid=float

TODO(Bereket): implement _evaluate(). Required rules:
- kill switch (settings.kill_switch or company_state["kill_switch"]) blocks everything
- banned claims (we never buy tickets for people, no "guaranteed tickets")
- sms only with consent + verified phone
- price only between PRICE_MIN_USD and PRICE_MAX_USD, at most one change per PRICE_CHANGE_COOLDOWN_MINUTES
- ad spend per day <= AD_BUDGET_USD_PER_DAY (company_state["ad_spend_today"])
- refund amount <= amount paid
- posts/ads: optional Claude review against community + ad-disclosure rules
- log every block as a DecisionLog with agent="compliance" so it shows on the Company Log
Until implemented, everything is ALLOWED so others can develop. Do not go live like this.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from app.enums import OutboundKind

if TYPE_CHECKING:
    from app.agents.base import AgentContext


@dataclass
class Verdict:
    allowed: bool
    reason: str = ""

    def __bool__(self) -> bool:
        return self.allowed


def check_outbound(ctx: "AgentContext", kind: OutboundKind, content: str = "", **meta: Any) -> Verdict:
    return _evaluate(ctx, kind, content, meta)


def _evaluate(ctx: "AgentContext", kind: OutboundKind, content: str, meta: dict) -> Verdict:
    # TODO(Bereket): real rules (see module docstring).
    return Verdict(True, "guardrails not implemented yet")
