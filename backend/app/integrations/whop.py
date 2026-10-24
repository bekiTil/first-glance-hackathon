"""Whop: everything that touches money. Owner: NATNAEL ONLY.

The Whop business, API key, payouts and webhook secret belong to Natnael's account.
Other agents call these functions (always after guardrails.check_outbound); nobody
else holds Whop credentials.

  create_checkout(watch_public_id, email, price_usd) -> checkout URL
  parse_webhook(body, headers)                        -> PaymentEvent | None
  refund(whop_payment_id, amount)                     -> bool
  update_price(price_usd)                             -> bool   (CEO agent)
  create_ad_draft(headline, body, budget_usd)         -> str    (Growth agent)

Docs: https://docs.whop.com/developer/quickstart  (API keys, webhooks)
      https://docs.whop.com/payments/create-checkout-link.md
      https://docs.whop.com/developer/guides/sandbox  (test here first)
"""

import json

from app.config import settings
from app.schemas import PaymentEvent


def create_checkout(watch_public_id: str, email: str, price_usd: float) -> str:
    if settings.mock_whop:
        # Simulates paying: app/api/dev.py fires the same handler a real webhook would.
        return f"{settings.public_api_url}/api/dev/fake-pay/{watch_public_id}"
    # TODO(Natnael): create a checkout for WHOP_PLAN_ID at price_usd with
    #   metadata {"watch_public_id": watch_public_id} (or match by email if metadata isn't
    #   supported) and redirect back to {PUBLIC_WEB_URL}/watch/{watch_public_id}?paid=1
    raise NotImplementedError("set MOCK_WHOP=true or implement Whop checkout")


def parse_webhook(body: bytes, headers: dict[str, str]) -> PaymentEvent | None:
    """Return None for webhook types we ignore. Raise ValueError on a bad signature."""
    if settings.mock_whop:
        return PaymentEvent.model_validate(json.loads(body))
    # TODO(Natnael): verify signature with WHOP_WEBHOOK_SECRET, handle payment succeeded,
    #   map to PaymentEvent(whop_payment_id, whop_user_id, email, watch_public_id, amount).
    raise NotImplementedError("set MOCK_WHOP=true or implement Whop webhook parsing")


def refund(whop_payment_id: str, amount: float) -> bool:
    if settings.mock_whop:
        return True
    # TODO(Natnael): Whop refund API for this payment.
    raise NotImplementedError


def update_price(price_usd: float) -> bool:
    if settings.mock_whop:
        return True
    # TODO(Natnael): update WHOP_PLAN_ID's price.
    raise NotImplementedError


def create_ad_draft(headline: str, body: str, budget_usd: float) -> str:
    if settings.mock_whop:
        return "mock-ad-draft"
    # TODO(Natnael): Whop ads API (draft only unless the CEO's budget allows).
    raise NotImplementedError
