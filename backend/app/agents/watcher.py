"""Watcher agent (the product). Owner: Bereket.

TODO(Bereket): implement run(). Spec:
- Runs every WATCH_INTERVAL_MINUTES (15). Find each Event (via WatchEvent) that has at least one
  Watch with status=active and starts_at in the future. Call tickets.best_listing(event) ONCE per
  event (not per watch); save event.lowest_price and event.checked_at.
- For each active watch on that event: deal_score.matches(listing, Checklist) must pass, and there must
  be no Alert yet with the same (watch_id, listing.key), so the same deal is never alerted twice.
- solari.verify_listing(listing, settings.data_dir / f"proof-{alert.token}.png"); skip if not ok.
- Create an Alert (listing JSON, listing_key, deal_score.score(listing, checklist, weights) where
  weights = ctx.get_state(StateKey.deal_weights, deal_score.DEFAULT_WEIGHTS), screenshot_path).
- Email: if ctx.check(OutboundKind.email, html) -> notify.send_email(...)
  Text:  if customer.phone and ctx.check(OutboundKind.sms, text, sms_consent=..., phone_verified=...)
         -> notify.send_sms(...)
  Links: {PUBLIC_API_URL}/go/{alert.token} (buy) and {PUBLIC_API_URL}/api/reply/{alert.token}/bought|keep|reject
  Text must end: "Reply 1=bought 2=keep watching 3=not what I wanted. STOP to opt out."
- Save alert.channels and alert.delivery_ids (proof it was sent); status failed if nothing was sent.
- ctx.log("sent_alert", reason, ...) per alert, ctx.log("checked_prices", ...) once per run.
"""

from app.agents.base import Agent, AgentContext
from app.config import settings
from app.enums import AgentName
from app.models import Job


class WatcherAgent(Agent):
    name = AgentName.watcher
    every_minutes = settings.watch_interval_minutes

    def run(self, ctx: AgentContext, job: Job | None = None) -> None:
        raise NotImplementedError("TODO(Bereket): watcher")
