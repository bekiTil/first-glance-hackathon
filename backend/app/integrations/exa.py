"""Exa web search for agents. Owner: Yared.

  search(query, n, include_domains) -> list[dict]   {title, url, text, published} for Growth/CEO research

Docs: https://exa.ai/docs/get-started/quickstart   Coupon: EXA50ZEROHUMAN
"""

from app.config import settings


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
