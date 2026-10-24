"""Whop: everything that touches money. Owner: NATNAEL ONLY.

The Whop business, API key, payouts and webhook secret belong to Natnael's account.
Other agents call these functions (always after guardrails.check_outbound); nobody
else holds Whop credentials.

  create_checkout(test_public_id, email, price_usd) -> checkout URL
  parse_webhook(body, headers)                        -> PaymentEvent | None
  refund(whop_payment_id, amount)                     -> bool
  update_price(price_usd)                             -> bool   (CEO agent)
  create_ad_draft(headline, body, budget_usd)         -> str    (Growth agent)

Docs: https://docs.whop.com/developer/quickstart  (API keys, webhooks)
      https://docs.whop.com/payments/create-checkout-link.md
      https://docs.whop.com/developer/guides/sandbox  (test here first)

Test against the sandbox first: set WHOP_API_BASE=https://sandbox-api.whop.com/api/v1 in .env.
"""

import base64
import hashlib
import hmac
import json
import logging
import time
import uuid

import httpx
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config import REPO_ROOT, settings
from app.schemas import PaymentEvent

log = logging.getLogger(__name__)

WEBHOOK_TOLERANCE_SECONDS = 5 * 60  # reject replays older than this (Standard Webhooks)
PAYMENT_SUCCEEDED = "payment.succeeded"


class _WhopSettings(BaseSettings):
    """Whop-only extras, read from the same .env without touching the shared config."""

    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")
    whop_api_base: str = "https://api.whop.com/api/v1"


_whop = _WhopSettings()


def create_checkout(test_public_id: str, email: str, price_usd: float) -> str:
    if settings.mock_whop:
        # Simulates paying: app/api/dev.py fires the same handler a real webhook would.
        return f"{settings.public_api_url}/api/dev/fake-pay/{test_public_id}"
    # The plan's price is kept in sync by update_price(); metadata is copied onto the payment,
    # which is how the webhook finds the test again (the Finance agent falls back to email).
    data = _request(
        "POST",
        "/checkout_configurations",
        json={
            "plan_id": settings.whop_plan_id,
            "metadata": {"test_public_id": test_public_id, "price_usd": f"{price_usd:.2f}"},
            "redirect_url": f"{settings.public_web_url}/report/{test_public_id}?paid=1",
        },
    )
    url = data.get("purchase_url")
    if not url:
        raise RuntimeError(f"Whop checkout has no purchase_url: {data}")
    return url if url.startswith("http") else f"https://whop.com{url}"


def parse_webhook(body: bytes, headers: dict[str, str]) -> PaymentEvent | None:
    """Return None for webhook types we ignore. Raise ValueError on a bad signature."""
    if settings.mock_whop:
        return PaymentEvent.model_validate(json.loads(body))
    headers = {k.lower(): v for k, v in headers.items()}
    _verify_signature(body, headers)

    event = json.loads(body)
    kind = event.get("type") or event.get("action")  # "action" on older API versions
    if kind != PAYMENT_SUCCEEDED:
        return None
    payment = event.get("data") or {}
    user = payment.get("user") or {}
    metadata = payment.get("metadata") or {}
    return PaymentEvent(
        whop_payment_id=payment["id"],
        whop_user_id=user.get("id"),
        email=payment.get("customer_email") or user.get("email"),
        # Empty if metadata didn't come through; the Finance agent then matches by email.
        test_public_id=str(metadata.get("test_public_id") or ""),
        amount=_money(payment.get("total") or payment.get("usd_total") or payment.get("final_amount")),
        currency=str(payment.get("currency") or "usd").lower(),
    )


def refund(whop_payment_id: str, amount: float) -> bool:
    if settings.mock_whop:
        return True
    try:
        _request(
            "POST",
            f"/payments/{whop_payment_id}/refund",
            json={"partial_amount": round(amount, 2)},
            headers={"Idempotency-Key": f"refund-{whop_payment_id}"},
        )
    except httpx.HTTPStatusError as e:
        log.error(
            "Whop refund failed for %s: %s %s", whop_payment_id, e.response.status_code, e.response.text
        )
        return False
    return True


def update_price(price_usd: float) -> bool:
    if settings.mock_whop:
        return True
    body = {"initial_price": round(price_usd, 2)}
    # Newer API versions call plans "variants"; try the original path first.
    for path in (f"/plans/{settings.whop_plan_id}", f"/variants/{settings.whop_plan_id}"):
        try:
            _request("PATCH", path, json=body)
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code != 404:
                log.error("Whop price update failed: %s %s", e.response.status_code, e.response.text)
                return False
    return False


def create_ad_draft(headline: str, body: str, budget_usd: float) -> str:
    if settings.mock_whop:
        return "mock-ad-draft"
    # Whop has no public API for creating ads, so drafts stay with us and nothing is spent.
    # Natnael launches a draft by hand in the Whop dashboard if the CEO's budget allows.
    draft_id = f"ad-draft-{uuid.uuid4().hex[:8]}"
    log.info("[ad draft %s] $%.2f/day: %s | %s", draft_id, budget_usd, headline, body[:200])
    return draft_id


def _request(method: str, path: str, *, json: dict, headers: dict[str, str] | None = None) -> dict:
    response = httpx.request(
        method,
        f"{_whop.whop_api_base.rstrip('/')}{path}",
        json=json,
        headers={"Authorization": f"Bearer {settings.whop_api_key}", **(headers or {})},
        timeout=20,
    )
    response.raise_for_status()
    return response.json() if response.content else {}


def _verify_signature(body: bytes, headers: dict[str, str]) -> None:
    """Standard Webhooks: base64(HMAC-SHA256(secret, f"{id}.{timestamp}.{body}")) in webhook-signature."""
    if not settings.whop_webhook_secret:
        raise ValueError("WHOP_WEBHOOK_SECRET is not set")
    msg_id = headers.get("webhook-id", "")
    timestamp = headers.get("webhook-timestamp", "")
    signatures = headers.get("webhook-signature", "")
    if not (msg_id and timestamp and signatures):
        raise ValueError("missing webhook signature headers")
    if not timestamp.isdigit() or abs(time.time() - int(timestamp)) > WEBHOOK_TOLERANCE_SECONDS:
        raise ValueError("bad or expired webhook timestamp")

    signed = f"{msg_id}.{timestamp}.".encode() + body
    for key in _secret_keys(settings.whop_webhook_secret):
        expected = base64.b64encode(hmac.new(key, signed, hashlib.sha256).digest()).decode()
        for candidate in signatures.split():
            _, _, sig = candidate.partition(",")
            if hmac.compare_digest(sig, expected):
                return
    raise ValueError("bad webhook signature")


def _secret_keys(secret: str) -> list[bytes]:
    # Whop's "ws_..." secrets are used as-is; generic Standard Webhooks "whsec_..." are base64.
    keys = [secret.encode()]
    if secret.startswith("whsec_"):
        keys.append(base64.b64decode(secret.removeprefix("whsec_")))
    return keys


def _money(value) -> float:
    """Whop amounts are a Money object {"amount": "15.00", ...} or, on older versions, a number."""
    if isinstance(value, dict):
        value = value.get("amount")
    return float(value or 0)
