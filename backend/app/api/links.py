"""Tracked buy links, email reply buttons, and proof screenshots. Owner: Bereket.

TODO(Bereket):
- GET /go/{token}: find Alert by token -> add Click -> status sent->clicked -> 302 to alert.listing["url"].
- GET /api/reply/{token}/{action}: enqueue(db, JobType.email_reply, ReplyIn(alert_id=..., action=...))
  -> 302 to {PUBLIC_WEB_URL}/thanks?action=<action>.
- GET /api/proof/{token}: FileResponse(alert.screenshot_path) or 404.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.api import todo
from app.db import get_db
from app.enums import ReplyAction

router = APIRouter(tags=["links"])


@router.get("/go/{token}")
def go(token: str, db: Session = Depends(get_db)) -> RedirectResponse:
    raise todo("Bereket", "tracked buy link")


@router.get("/api/reply/{token}/{action}")
def reply(token: str, action: ReplyAction, db: Session = Depends(get_db)) -> RedirectResponse:
    raise todo("Bereket", "email reply button")


@router.get("/api/proof/{token}")
def proof(token: str, db: Session = Depends(get_db)) -> FileResponse:
    raise todo("Bereket", "proof screenshot")
