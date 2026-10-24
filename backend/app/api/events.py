"""Free NYC events page (draws visitors in). Owner: Yared."""

import time

from fastapi import APIRouter, HTTPException

from app.integrations import exa
from app.schemas import FreeEvent

router = APIRouter(prefix="/api/free-events", tags=["events"])

_CACHE: dict[str, tuple[float, list[FreeEvent]]] = {}
_TTL_SECONDS = 30 * 60  # don't burn Exa credits on every page view


@router.get("", response_model=list[FreeEvent])
def free_events(when: str = "tonight") -> list[FreeEvent]:
    key = when.strip().lower()[:40] or "tonight"
    cached = _CACHE.get(key)
    if cached and time.time() - cached[0] < _TTL_SECONDS:
        return cached[1]
    try:
        events = exa.free_events(key)
    except Exception as e:
        if cached:
            return cached[1]
        raise HTTPException(502, f"event search failed: {e}") from e
    _CACHE[key] = (time.time(), events)
    return events
