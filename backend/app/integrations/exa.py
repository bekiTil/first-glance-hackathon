"""Exa web search for agents. Owner: Yared.

  free_events(when) -> list[FreeEvent]   free NYC events (Luma, Eventbrite) for the free page
  search(query, n)  -> list[dict]        {title, url, text, published} for Growth/CEO research

Docs: https://exa.ai/docs/get-started/quickstart   Coupon: EXA50ZEROHUMAN
"""

from app.config import settings
from app.schemas import FreeEvent

EVENT_DOMAINS = ["lu.ma", "luma.com", "eventbrite.com"]


def _client():
    from exa_py import Exa

    return Exa(api_key=settings.exa_api_key)


def search(query: str, n: int = 5, include_domains: list[str] | None = None) -> list[dict]:
    if settings.mock_exa:
        return [
            {
                "title": f"Mock result for {query}",
                "url": "https://example.com",
                "text": "...",
                "published": None,
            }
        ][:n]
    response = _client().search(
        query, num_results=n, include_domains=include_domains, contents={"text": True}
    )
    return [
        {
            "title": r.title or r.url,
            "url": r.url,
            "text": (getattr(r, "text", None) or "")[:1500],
            "published": getattr(r, "published_date", None),
        }
        for r in response.results
    ]


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
    results = search(f"free event in New York City {when}", n=10, include_domains=EVENT_DOMAINS)
    return [
        FreeEvent(title=r["title"], url=r["url"], when=when, summary=r["text"][:240] or None) for r in results
    ]
