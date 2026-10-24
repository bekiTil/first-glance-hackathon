"""Free NYC events page (draws visitors in). Owner: Yared.

TODO(Yared): return exa.free_events(when); cache ~30 min so page views don't burn Exa credits.
"""

from fastapi import APIRouter

from app.api import todo
from app.schemas import FreeEvent

router = APIRouter(prefix="/api/free-events", tags=["events"])


@router.get("", response_model=list[FreeEvent])
def free_events(when: str = "tonight") -> list[FreeEvent]:
    raise todo("Yared", "free events")
