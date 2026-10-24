"""Checklist matching + deal score. Owner: Bereket.

SHARED contract: DEFAULT_WEIGHTS is the format of company_state["deal_weights"]. Yared's Research
agent writes learned weights in exactly this shape (same keys, floats); the Watcher reads them.

TODO(Bereket):
- matches(): requirements = the guarantee. Fail if price > max_price_per_ticket, date outside
  date_from..date_to, weekday not in weekdays (when given), quantity_available < quantity, or the
  section matches any exclude_sections. Return (ok, list of human-readable failed checks).
- score(): 0..1, ranking only. v1 = cheaper is better. v2 = use the weights (price, lower_level, weekend).
"""

from app.schemas import Checklist, Listing

DEFAULT_WEIGHTS: dict[str, float] = {"price": 1.0, "lower_level": 0.0, "weekend": 0.0}


def matches(listing: Listing, checklist: Checklist) -> tuple[bool, list[str]]:
    raise NotImplementedError("TODO(Bereket): matches")


def score(listing: Listing, checklist: Checklist, weights: dict | None = None) -> float:
    raise NotImplementedError("TODO(Bereket): score")
