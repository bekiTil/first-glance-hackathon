"""Read a customer's page + write our rewrite. Owner: Bereket.

Called synchronously by POST /api/tests (the customer is waiting on the page, keep it < ~20 s).

TODO(Bereket): implement both. Spec:
- read_hero(url): fetch the page (httpx, follow redirects, browser-like User-Agent, 10 s timeout);
  pull the visible hero: <h1> (or og:title / <title>), the first meaningful paragraph or meta
  description, and the main button text. If the HTML is empty (JS-rendered site), use Solari to
  render it. Optionally llm.ask_json to pick the right pieces from the page text. Return HeroCopy.
  Raise ValueError("couldn't read that page") for unreachable/private pages (API returns 422).
- write_rewrite(original, what_you_do): llm.ask_json -> HeroCopy that a stranger would understand
  in 5 seconds: say WHAT it is and FOR WHOM in plain words, keep their tone, no hype, no invented
  claims, similar length. Pass a realistic mock= so MOCK_LLM=true still works.
"""

from app.schemas import HeroCopy


def read_hero(url: str) -> HeroCopy:
    raise NotImplementedError("TODO(Bereket): read_hero")


def write_rewrite(original: HeroCopy, what_you_do: str) -> HeroCopy:
    raise NotImplementedError("TODO(Bereket): write_rewrite")
