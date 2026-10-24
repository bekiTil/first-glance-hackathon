"""Email (Resend) and text (Twilio). Owner: Natnael.

  send_email(to, subject, html) -> delivery id
  send_sms(to, body)            -> delivery id

Mock mode prints the message and appends it to OUTBOX (tests read it).
Texting: US numbers need carrier registration (days). Until then use a Twilio trial
number, which can only text pre-verified numbers (fine for the demo).
"""

import logging
import uuid

import resend
from twilio.rest import Client

from app.config import settings

log = logging.getLogger(__name__)

OUTBOX: list[dict] = []
_twilio: Client | None = None


def send_email(to: str, subject: str, html: str) -> str:
    if settings.mock_notify:
        return _mock("email", to, f"{subject}\n{html}")
    resend.api_key = settings.resend_api_key
    sent = resend.Emails.send({"from": settings.email_from, "to": [to], "subject": subject, "html": html})
    return sent["id"]


def send_sms(to: str, body: str) -> str:
    if settings.mock_notify:
        return _mock("sms", to, body)
    global _twilio
    if _twilio is None:
        _twilio = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    return _twilio.messages.create(to=to, from_=settings.twilio_from_number, body=body).sid


def _mock(channel: str, to: str, body: str) -> str:
    delivery_id = f"mock-{uuid.uuid4().hex[:8]}"
    OUTBOX.append({"channel": channel, "to": to, "body": body, "id": delivery_id})
    log.info("[mock %s -> %s] %s", channel, to, body[:200])
    return delivery_id
