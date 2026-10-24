"""'My watches' with a one-time email login link (no passwords). Owner: Natnael.

TODO(Natnael):
- POST /login: if a Customer has that email, create a LoginToken (24h) and email
  {PUBLIC_WEB_URL}/me?token=<token>. Always return the same OkOut message (don't reveal which emails exist).
- GET /watches?token=: valid unexpired token -> that customer's watches as list[WatchOut]; else 401.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import todo
from app.db import get_db
from app.schemas import LoginRequest, OkOut, WatchOut

router = APIRouter(prefix="/api/me", tags=["me"])


@router.post("/login", response_model=OkOut)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> OkOut:
    raise todo("Natnael", "magic-link login")


@router.get("/watches", response_model=list[WatchOut])
def my_watches(token: str, db: Session = Depends(get_db)) -> list[WatchOut]:
    raise todo("Natnael", "my watches")
