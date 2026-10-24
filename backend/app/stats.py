"""Company numbers: shown on the Company Log page and read by the CEO agent. Owner: Bereket.

Customer tests only (not kind=self): revenue = sum of succeeded Payment.amount; payments/refunds counts;
tests created / paid (have a payment) / delivered (results graded, even if later refunded);
rewrite_win_rate = delivered tests with results.winner == "rewrite" / delivered;
conversion = paid / created; price = company_state["price_usd"] or STARTING_PRICE_USD.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.enums import PaymentStatus, StateKey, TestKind, Winner
from app.models import CompanyState, PageTest, Payment
from app.schemas import Stats


def current_price(db: Session) -> float:
    row = db.get(CompanyState, str(StateKey.price_usd))
    try:
        return float(row.value) if row and row.value is not None else settings.starting_price_usd
    except (TypeError, ValueError):
        return settings.starting_price_usd


def compute_stats(db: Session) -> Stats:
    customer = PageTest.kind == TestKind.customer
    payments = db.execute(
        select(Payment.amount, Payment.status, Payment.test_id)
        .join(PageTest, PageTest.id == Payment.test_id)
        .where(customer)
    ).all()
    created = int(db.scalar(select(func.count(PageTest.id)).where(customer)) or 0)
    delivered = db.scalars(select(PageTest.results).where(customer, PageTest.delivered_at.is_not(None))).all()
    wins = sum(1 for r in delivered if (r or {}).get("winner") == Winner.rewrite)
    paid = len({p.test_id for p in payments})
    return Stats(
        revenue_usd=round(sum(p.amount for p in payments if p.status == PaymentStatus.succeeded), 2),
        payments=len(payments),
        refunds=sum(1 for p in payments if p.status == PaymentStatus.refunded),
        tests_created=created,
        tests_paid=paid,
        tests_delivered=len(delivered),
        rewrite_win_rate=round(wins / len(delivered), 4) if delivered else 0.0,
        conversion_rate=round(paid / created, 4) if created else 0.0,
        price_usd=current_price(db),
    )
