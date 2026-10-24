"""Screenshots of customers' pages with a Solari headless browser. Owner: Bereket.

  screenshot(url, save_as) -> saved path, or None
  render_html(url)         -> the page's HTML after JavaScript ran, or None

Used for the report (what their page looked like when tested) and to read pages that need
JavaScript to render. Public pages only: no logins, no captcha solving.
Docs: https://getsolari.com  SDK: pip package `solari-browser` (already a dependency).
Neither function raises: a page that can't be loaded returns None.
"""

import asyncio
import logging
from pathlib import Path

from app.config import settings

log = logging.getLogger(__name__)

PAGE_TIMEOUT_MS = 30_000
SETTLE_MS = 2_500  # let client-side rendering and hero animations finish


def screenshot(url: str, save_as: Path) -> str | None:
    if settings.mock_solari:
        return None
    return _run(url, save_as)


def render_html(url: str) -> str | None:
    if settings.mock_solari:
        return None
    return _run(url, None)


def _run(url: str, save_as: Path | None) -> str | None:
    if not settings.solari_api_key:
        log.warning("SOLARI_API_KEY is not set; skipping %s", url)
        return None
    try:
        return asyncio.run(_open(url, save_as))
    except Exception as e:
        log.warning("solari could not load %s: %s", url, e)
        return None


async def _open(url: str, save_as: Path | None) -> str | None:
    from solari_browser import Solari

    async with Solari(api_key=settings.solari_api_key) as solari:
        browser = await solari.launch()
        try:
            page = await browser.new_page()
            await page.set_viewport_size({"width": 1366, "height": 900})
            response = await page.goto(url, wait_until="load", timeout=PAGE_TIMEOUT_MS)
            if response is not None and response.status >= 400:
                log.warning("solari: %s returned HTTP %s", url, response.status)
                return None
            await page.wait_for_timeout(SETTLE_MS)
            if save_as is None:
                return await page.content()
            save_as.parent.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=str(save_as), full_page=True)
            return str(save_as)
        finally:
            await browser.close()
