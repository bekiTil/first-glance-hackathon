"""Study content + analysis for the Research agent. Owner: Yared.

Each round shows 5 sets of 3 real-looking Knicks listings that trade price against seat level and
day of week, then asks "would you pay $3 for this?" about the current landing copy.

Scoring formula (Bereket: deal_score.score() should use the same one so the Watcher ranks like this):
    score = (w_price * (1 - price / max_price) + w_lower * lower_level + w_weekend * weekend) / sum(w)
"""

from itertools import product

from app.schemas import LandingCopy, StudyOption, StudySet

ROUNDS: dict[int, list[StudySet]] = {}


def _set(event: str, *options: tuple) -> StudySet:
    return StudySet(
        event=event,
        options=[
            StudyOption(
                label=label, price=price, section=section, lower_level=lower, day=day, weekend=weekend
            )
            for label, price, section, lower, day, weekend in options
        ],
    )


ROUNDS[1] = [
    _set(
        "Knicks vs. Celtics at MSG",
        ("A", 62, "Section 224 (upper)", False, "Tue Nov 10", False),
        ("B", 79, "Section 109 (lower)", True, "Fri Nov 13", True),
        ("C", 71, "Section 112 (lower)", True, "Wed Nov 11", False),
    ),
    _set(
        "Knicks vs. Heat at MSG",
        ("A", 55, "Section 226 (upper)", False, "Mon Nov 16", False),
        ("B", 68, "Section 203 (upper)", False, "Sat Nov 21", True),
        ("C", 84, "Section 104 (lower)", True, "Thu Nov 19", False),
    ),
    _set(
        "Knicks vs. 76ers at MSG",
        ("A", 74, "Section 117 (lower)", True, "Tue Nov 24", False),
        ("B", 66, "Section 210 (upper)", False, "Fri Nov 27", True),
        ("C", 90, "Section 102 (lower)", True, "Sat Nov 28", True),
    ),
    _set(
        "Knicks vs. Bulls at MSG",
        ("A", 48, "Section 228 (upper)", False, "Wed Dec 2", False),
        ("B", 58, "Section 221 (upper)", False, "Sun Dec 6", True),
        ("C", 64, "Section 115 (lower)", True, "Tue Dec 1", False),
    ),
    _set(
        "Knicks vs. Nets at MSG",
        ("A", 70, "Section 205 (upper)", False, "Fri Dec 4", True),
        ("B", 77, "Section 110 (lower)", True, "Thu Dec 3", False),
        ("C", 95, "Section 106 (lower)", True, "Sat Dec 5", True),
    ),
]

ROUNDS[2] = [
    _set(
        "Knicks vs. Bucks at MSG",
        ("A", 59, "Section 223 (upper)", False, "Mon Dec 7", False),
        ("B", 76, "Section 113 (lower)", True, "Fri Dec 11", True),
        ("C", 67, "Section 207 (upper)", False, "Sat Dec 12", True),
    ),
    _set(
        "Knicks vs. Hawks at MSG",
        ("A", 52, "Section 225 (upper)", False, "Tue Dec 15", False),
        ("B", 69, "Section 108 (lower)", True, "Wed Dec 16", False),
        ("C", 88, "Section 101 (lower)", True, "Sat Dec 19", True),
    ),
    _set(
        "Knicks vs. Cavaliers at MSG",
        ("A", 81, "Section 111 (lower)", True, "Sun Dec 20", True),
        ("B", 63, "Section 212 (upper)", False, "Fri Dec 18", True),
        ("C", 57, "Section 227 (upper)", False, "Mon Dec 21", False),
    ),
    _set(
        "Knicks vs. Magic at MSG",
        ("A", 46, "Section 229 (upper)", False, "Tue Dec 22", False),
        ("B", 61, "Section 116 (lower)", True, "Wed Dec 23", False),
        ("C", 72, "Section 105 (lower)", True, "Sat Dec 26", True),
    ),
    _set(
        "Knicks vs. Raptors at MSG",
        ("A", 66, "Section 214 (upper)", False, "Sat Jan 2", True),
        ("B", 73, "Section 114 (lower)", True, "Thu Dec 31", False),
        ("C", 54, "Section 230 (upper)", False, "Tue Dec 29", False),
    ),
]

DEFAULT_LANDING = LandingCopy(
    headline="Tell us your max price. We'll text you when tickets drop under it.",
    subhead="An AI agent checks SeatGeek and Ticketmaster every 15 minutes for Knicks, Broadway and concerts.",
    bullets=["$3 per watch", "Refunded automatically if we never find a match", "Run entirely by AI agents"],
    version=1,
)

V1_WEIGHTS = {"price": 1.0, "lower_level": 0.0, "weekend": 0.0}  # "cheapest wins"


def option_score(option: StudyOption, max_price: float, weights: dict) -> float:
    w = {**V1_WEIGHTS, **weights}
    total = (w["price"] + w["lower_level"] + w["weekend"]) or 1.0
    price_part = max(0.0, 1 - option.price / max(max_price, 1))
    return (
        w["price"] * price_part + w["lower_level"] * option.lower_level + w["weekend"] * option.weekend
    ) / total


def predict(study_set: StudySet, weights: dict) -> str:
    max_price = max(o.price for o in study_set.options)
    return max(study_set.options, key=lambda o: option_score(o, max_price, weights)).label


def agreement(sets: list[StudySet], picks: list[tuple[int, str]], weights: dict) -> float:
    """Share of human picks the weighted model predicts. picks = [(set_index, label), ...]"""
    if not picks:
        return 0.0
    hits = sum(1 for i, label in picks if 0 <= i < len(sets) and predict(sets[i], weights) == label)
    return round(hits / len(picks), 3)


def fit_weights(sets: list[StudySet], picks: list[tuple[int, str]]) -> dict:
    """Grid search the weights that best agree with what real people picked (price fixed at 1)."""
    grid = [x / 10 for x in range(0, 21)]
    best, best_score = dict(V1_WEIGHTS), -1.0
    for lower, weekend in product(grid, grid):
        weights = {"price": 1.0, "lower_level": lower, "weekend": weekend}
        score = agreement(sets, picks, weights)
        # prefer smaller weights on ties so we don't overfit
        if score > best_score + 1e-9 or (
            abs(score - best_score) < 1e-9 and lower + weekend < sum(best.values()) - 1
        ):
            best, best_score = weights, score
    return best
