"""Phone verification (6-digit code by text). Owner: Natnael.

TODO(Natnael):
- POST /send-code: find Watch by public id -> set customer.phone, phone_verified=False -> store a
  PhoneCode (hash the code, expires in ~10 min) -> notify.send_sms(phone, "Ticket Watch code: ...").
  In mock mode (MOCK_NOTIFY=true) use the fixed code 123456 so anyone can test.
- POST /verify: newest unused, unexpired PhoneCode for the phone matches -> mark used ->
  customer.phone_verified=True -> VerifyOut(verified=True); otherwise verified=False.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import todo
from app.db import get_db
from app.schemas import OkOut, SendCodeRequest, VerifyCodeRequest, VerifyOut

router = APIRouter(prefix="/api/phone", tags=["phone"])

MOCK_CODE = "123456"


@router.post("/send-code", response_model=OkOut)
def send_code(body: SendCodeRequest, db: Session = Depends(get_db)) -> OkOut:
    raise todo("Natnael", "send phone code")


@router.post("/verify", response_model=VerifyOut)
def verify_code(body: VerifyCodeRequest, db: Session = Depends(get_db)) -> VerifyOut:
    raise todo("Natnael", "verify phone code")
