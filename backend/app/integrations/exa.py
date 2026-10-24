"""Exa web search for agents. Owner: Yared.

  free_events(when)        -> list[FreeEvent]   free NYC events (Luma, Eventbrite...) for the free page
  search(query, n)         -> list[dict]        {title, url, text} for Growth/CEO research

Docs: https://exa.ai/docs/get-started/quickstart   Coupon: EXA50ZEROHUMAN
"""

from app.config import settings
from app.schemas import FreeEvent


def free_events(when: str = "tonight") -> list[FreeEvent]:
    if settings.mock_exa:
        return [
            FreeEvent(
                title="NYC AI Builders Meetup", url="https://lu.ma/example", when=when, where="Williamsburg"
            ),
            FreeEvent(
                title="Free Jazz in the Park",
                url="https://www.eventbrite.com/e/example",
                when=when,
                where="Prospect Park",
            ),
        ]
    # TODO(Yared): exa_py.Exa(settings.exa_api_key) search restricted to lu.ma / eventbrite.com
    #   for f"free events in NYC {when}", map results -> FreeEvent.
    raise NotImplementedError("set MOCK_EXA=true or implement Exa free events")


def search(query: str, n: int = 5) -> list[dict]:
    if settings.mock_exa:
        return [{"title": f"Mock result for {query}", "url": "https://example.com", "text": "..."}][:n]
    # TODO(Yared): exa_py search with text contents.
    raise NotImplementedError("set MOCK_EXA=true or implement Exa search")
