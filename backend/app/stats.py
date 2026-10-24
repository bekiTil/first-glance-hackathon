"""Company numbers: shown on the Company Log page and read by the CEO agent. Owner: Bereket.

TODO(Bereket): fill every field of schemas.Stats from the tables:
revenue = sum of succeeded Payment.amount; payments/refunds counts; watches created/active;
alerts sent (not failed); clicks; purchases (alerts with status bought);
conversion = payments / watches created; price = company_state["price_usd"] or STARTING_PRICE_USD.
"""

from sqlalchemy.orm import Session

from app.schemas import Stats


def compute_stats(db: Session) -> Stats:
    raise NotImplementedError("TODO(Bereket): stats")
