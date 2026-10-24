"""Ticket data (read-only APIs; we never buy). Owner: Bereket.

  search_events(checklist)  -> list[EventInfo]   events matching performer + date range
  best_listing(event)       -> Listing | None    current lowest price for one event

Real sources: SeatGeek (main: per-event lowest price) and Ticketmaster Discovery
(5,000 calls/day, 5/sec). Mock mode returns fake events with prices that drift
every 15 minutes, so the watcher produces alerts locally.
"""

import hashlib
import time as time_module
from datetime import datetime, time, timedelta

from app.config import settings
from app.enums import TicketSource
from app.models import Event
from app.schemas import Checklist, EventInfo, Listing

# Tests can pin the mock price: tickets.MOCK_PRICE_OVERRIDE = 60.0
MOCK_PRICE_OVERRIDE: float | None = None


def search_events(checklist: Checklist) -> list[EventInfo]:
    if settings.mock_tickets:
        return _mock_events(checklist)
    # TODO(Bereket): SeatGeek GET https://api.seatgeek.com/2/events
    #   params: q=checklist.performer, datetime_utc.gte/lte, client_id=settings.seatgeek_client_id
    #   map each event -> EventInfo(source=seatgeek, external_id=str(id), name=title,
    #   starts_at=datetime_utc, venue=venue.name, url=url); filter by checklist.weekdays.
    #   Optionally merge Ticketmaster Discovery results.
    raise NotImplementedError("set MOCK_TICKETS=true or implement SeatGeek search")


def best_listing(event: Event) -> Listing | None:
    if settings.mock_tickets:
        return _mock_listing(event)
    # TODO(Bereket): SeatGeek GET /2/events/{external_id} -> stats.lowest_price (+ url).
    #   Prices from the API may exclude fees: set includes_fees=False and let Solari confirm.
    raise NotImplementedError("set MOCK_TICKETS=true or implement SeatGeek lowest price")


# ---------- mock ----------


def _mock_events(checklist: Checklist) -> list[EventInfo]:
    events: list[EventInfo] = []
    day = checklist.date_from
    while day <= checklist.date_to and len(events) < 6:
        if not checklist.weekdays or day.weekday() in checklist.weekdays:
            ext = f"mock-{checklist.performer.lower().replace(' ', '-')}-{day.isoformat()}"
            events.append(
                EventInfo(
                    source=TicketSource.mock,
                    external_id=ext,
                    name=f"{checklist.performer} vs. Mock Rivals",
                    starts_at=datetime.combine(day, time(23, 30)),  # 7:30pm ET in UTC
                    venue=checklist.venue or "Madison Square Garden",
                    url=f"https://example.com/tickets/{ext}",
                )
            )
        day += timedelta(days=1)
    return events


def _mock_listing(event: Event) -> Listing:
    if MOCK_PRICE_OVERRIDE is not None:
        price = MOCK_PRICE_OVERRIDE
    else:
        bucket = int(time_module.time() // (settings.watch_interval_minutes * 60))
        h = int(hashlib.sha256(f"{event.external_id}:{bucket}".encode()).hexdigest(), 16)
        price = 55 + (h % 70)  # $55-$124, changes every interval
    return Listing(
        source=TicketSource.mock,
        external_event_id=event.external_id,
        event_name=event.name,
        starts_at=event.starts_at,
        venue=event.venue,
        price_per_ticket=float(price),
        includes_fees=True,
        quantity_available=4,
        section="Section 105" if price > 90 else "Section 210",
        url=event.url,
    )
