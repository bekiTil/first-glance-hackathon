"""Live-listing check with a Solari headless browser. Owner: Bereket.

  verify_listing(listing, save_as) -> Verification

Opens the public listing page, reads the all-in price, saves a screenshot as proof the
deal existed. Only public pages: no logins, never touch checkout.
Docs: https://getsolari.com  SDK: pip package `solari-browser` (already a dependency).
"""

from pathlib import Path

from app.config import settings
from app.schemas import Listing, Verification


def verify_listing(listing: Listing, save_as: Path) -> Verification:
    if settings.mock_solari:
        return Verification(ok=True, price_seen=listing.price_per_ticket, screenshot_path=None, note="mock")
    # TODO(Bereket): with solari-browser, open listing.url, wait for price element,
    #   parse the all-in price, page.screenshot(path=save_as); return ok=False if the
    #   listing is gone or the price is above the checklist max.
    raise NotImplementedError("set MOCK_SOLARI=true or implement Solari verification")
