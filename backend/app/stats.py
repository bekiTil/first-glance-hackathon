"""Company numbers: shown on the Company Log page and read by the CEO agent. Owner: Bereket.

TODO(Bereket): fill every field of schemas.Stats from the tables (customer tests only, not kind=self):
revenue = sum of succeeded Payment.amount; payments/refunds counts; tests created/paid/delivered;
rewrite_win_rate = delivered customer tests with results.winner == "rewrite" / delivered;
conversion = paid / created; price = company_state["price_usd"] or STARTING_PRICE_USD.
"""

from sqlalchemy.orm import Session

from app.schemas import Stats


def compute_stats(db: Session) -> Stats:
    raise NotImplementedError("TODO(Bereket): stats")
