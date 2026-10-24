"""Inbound webhooks: Whop payments + Twilio texts. Owner: Natnael.

Rule: routes only enqueue jobs (app.jobs.enqueue); Finance/Support agents do the work.
TODO(Natnael):
- POST /whop: whop.parse_webhook(body, headers) -> PaymentEvent | None (ValueError = bad signature
  -> 400) -> enqueue(db, JobType.payment_received, event.model_dump(mode="json")) -> OkOut.
- POST /sms: validate X-Twilio-Signature -> enqueue(db, JobType.sms_received,
  ReplyIn(phone=From, text=Body).model_dump(mode="json")) -> empty TwiML "<Response></Response>".
"""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api import todo
from app.db import get_db
from app.schemas import OkOut

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/whop", response_model=OkOut)
async def whop_webhook(request: Request, db: Session = Depends(get_db)) -> OkOut:
    raise todo("Natnael", "Whop webhook")


@router.post("/sms")
def twilio_sms(From: str = Form(...), Body: str = Form(""), db: Session = Depends(get_db)) -> Response:  # noqa: N803
    raise todo("Natnael", "Twilio incoming text")
