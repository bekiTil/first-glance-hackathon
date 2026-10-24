"""Create/confirm a watch. Owner: Bereket (the confirm route calls Natnael's whop.create_checkout).

TODO(Bereket):
- POST ""  : intake.build_checklist(query, today) -> find/create Customer by email (set phone,
             phone_verified=False if the phone changed, sms_consent) -> Watch(status=draft) ->
             tickets.search_events(checklist) -> upsert Event rows + WatchEvent links ->
             DecisionLog(agent=watcher, action="built_checklist") -> WatchOut.
- GET  /{id}: WatchOut for Watch.public_id (never expose the integer id).
- PATCH /{id}: only while draft; replace checklist, clear questions, re-attach events.
- POST /{id}/confirm: only draft/awaiting_payment -> whop.create_checkout(public_id, email, price)
             where price = company_state["price_usd"] or settings.starting_price_usd ->
             status=awaiting_payment -> CheckoutOut.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import todo
from app.db import get_db
from app.schemas import CheckoutOut, CreateWatchRequest, UpdateChecklistRequest, WatchOut

router = APIRouter(prefix="/api/watches", tags=["watches"])


@router.post("", response_model=WatchOut)
def create_watch(body: CreateWatchRequest, db: Session = Depends(get_db)) -> WatchOut:
    raise todo("Bereket", "create watch")


@router.get("/{public_id}", response_model=WatchOut)
def get_watch(public_id: str, db: Session = Depends(get_db)) -> WatchOut:
    raise todo("Bereket", "get watch")


@router.patch("/{public_id}", response_model=WatchOut)
def update_checklist(public_id: str, body: UpdateChecklistRequest, db: Session = Depends(get_db)) -> WatchOut:
    raise todo("Bereket", "update checklist")


@router.post("/{public_id}/confirm", response_model=CheckoutOut)
def confirm_watch(public_id: str, db: Session = Depends(get_db)) -> CheckoutOut:
    raise todo("Bereket", "confirm watch")
