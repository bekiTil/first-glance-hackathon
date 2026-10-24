"""Email (Resend) and text (Twilio). Owner: Natnael.

  send_email(to, subject, html) -> delivery id
  send_sms(to, body)            -> delivery id

Mock mode prints the message and appends it to OUTBOX (tests read it).
Texting: US numbers need carrier registration (days). Until then use a Twilio trial
number, which can only text pre-verified numbers (fine for the demo).
"""

import logging
import uuid

from app.config import settings

log = logging.getLogger(__name__)

OUTBOX: list[dict] = []


def send_email(to: str, subject: str, html: str) -> str:
    if settings.mock_notify:
        return _mock("email", to, f"{subject}\n{html}")
    # TODO(Natnael): send with Resend (package `resend`, already a dependency) from
    #   settings.email_from using settings.resend_api_key; return Resend's message id.
    raise NotImplementedError("set MOCK_NOTIFY=true or implement Resend email")


def send_sms(to: str, body: str) -> str:
    if settings.mock_notify:
        return _mock("sms", to, body)
    # TODO(Natnael): send with Twilio (package `twilio`, already a dependency) from
    #   settings.twilio_from_number; return the message SID.
    raise NotImplementedError("set MOCK_NOTIFY=true or implement Twilio text")


def _mock(channel: str, to: str, body: str) -> str:
    delivery_id = f"mock-{uuid.uuid4().hex[:8]}"
    OUTBOX.append({"channel": channel, "to": to, "body": body, "id": delivery_id})
    log.info("[mock %s -> %s] %s", channel, to, body[:200])
    return delivery_id
