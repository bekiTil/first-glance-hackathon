"""Screenshots of customers' pages with a Solari headless browser. Owner: Bereket.

  screenshot(url, save_as) -> saved path, or None

Used for the report (what their page looked like when tested) and to read pages that need
JavaScript to render. Public pages only: no logins.
Docs: https://getsolari.com  SDK: pip package `solari-browser` (already a dependency).
"""

from pathlib import Path

from app.config import settings


def screenshot(url: str, save_as: Path) -> str | None:
    if settings.mock_solari:
        return None
    # TODO(Bereket): open url with solari-browser, wait for load, save a full-page PNG to save_as,
    #   return str(save_as). Return None (don't raise) if the page can't be loaded.
    raise NotImplementedError("set MOCK_SOLARI=true or implement Solari screenshots")
