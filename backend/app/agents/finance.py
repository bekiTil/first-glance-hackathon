"""Finance agent. Owner: Natnael (the only person who handles money).

- job payment_received (payload = schemas.PaymentEvent): ignore duplicates (same whop_payment_id);
  find the PageTest by test_public_id (or the customer's newest unpaid test if Whop dropped the
  metadata); save a Payment row; PageTest.status=paid, price_paid=amount; store whop_user_id on the
  Customer; enqueue run_test so the Tester starts right away. ctx.log("payment_recorded", ...).
- every 10 min (job is None): the money-back guarantee, decided from our own records only:
    delivered customer tests whose results.winner != "rewrite"  -> refund
    tests stuck in paid/testing/failed for > 3 hours             -> refund
  For each: if ctx.check(OutboundKind.refund, amount=..., amount_paid=...): whop.refund(...),
  Payment.status=refunded, PageTest.status=refunded, email the customer, ctx.log("refunded", why).
  Once an hour it also logs a short summary of the books.
"""

import html
from datetime import timedelta

from sqlalchemy import func, select

from app.agents.base import Agent, AgentContext
from app.config import settings
from app.db_time import utcnow
from app.enums import AgentName, JobType, OutboundKind, PaymentStatus, TestKind, TestStatus, Winner
from app.integrations import notify, whop
from app.jobs import enqueue
from app.models import Customer, DecisionLog, Job, PageTest, Payment
from app.schemas import PaymentEvent

UNPAID = (TestStatus.draft, TestStatus.awaiting_payment)
STUCK = (TestStatus.paid, TestStatus.testing, TestStatus.failed)
STUCK_AFTER = timedelta(hours=3)
SUMMARY_EVERY = timedelta(hours=1)


class FinanceAgent(Agent):
    name = AgentName.finance
    every_minutes = 10
    handles = (JobType.payment_received,)

    def run(self, ctx: AgentContext, job: Job | None = None) -> None:
        if job is None:
            self._money_back_guarantee(ctx)
        else:
            self._record_payment(ctx, PaymentEvent.model_validate(job.payload))

    # ---------- payments ----------

    def _record_payment(self, ctx: AgentContext, event: PaymentEvent) -> None:
        db = ctx.db
        if db.scalar(select(Payment).where(Payment.whop_payment_id == event.whop_payment_id)):
            ctx.log(
                "duplicate_payment_ignored",
                "Whop sent this payment twice; it is already on the books.",
                whop_payment_id=event.whop_payment_id,
            )
            return

        test = self._find_test(ctx, event)
        if test is None:
            ctx.log(
                "payment_unmatched",
                "A payment arrived that matches no test; it needs a human look.",
                whop_payment_id=event.whop_payment_id,
                amount=event.amount,
            )
            return

        db.add(
            Payment(
                whop_payment_id=event.whop_payment_id,
                whop_user_id=event.whop_user_id,
                test_id=test.id,
                amount=event.amount,
                currency=event.currency,
                status=PaymentStatus.succeeded,
            )
        )
        customer = db.get(Customer, test.customer_id) if test.customer_id else None
        if customer and event.whop_user_id and customer.whop_user_id != event.whop_user_id:
            if db.scalar(select(Customer).where(Customer.whop_user_id == event.whop_user_id)) is None:
                customer.whop_user_id = event.whop_user_id

        if test.status in UNPAID:
            test.status = TestStatus.paid
            test.price_paid = event.amount
            enqueue(db, JobType.run_test, {"test_id": test.public_id})
            reason = f"Received ${event.amount:.2f} on Whop; handed the test to the Tester to launch."
        else:
            # Paid twice: keep it on record (the guarantee still covers it), don't restart the test.
            reason = f"Received ${event.amount:.2f} for a test that was already {test.status}."
        db.flush()
        ctx.log(
            "payment_recorded",
            reason,
            test_id=test.public_id,
            amount=event.amount,
            currency=event.currency,
            test_status=test.status,
        )

    def _find_test(self, ctx: AgentContext, event: PaymentEvent) -> PageTest | None:
        if event.test_public_id:
            return ctx.db.scalar(select(PageTest).where(PageTest.public_id == event.test_public_id))
        if not event.email:
            return None
        return ctx.db.scalar(
            select(PageTest)
            .join(Customer, Customer.id == PageTest.customer_id)
            .where(func.lower(Customer.email) == event.email.lower(), PageTest.status.in_(UNPAID))
            .order_by(PageTest.created_at.desc())
            .limit(1)
        )

    # ---------- the money-back guarantee ----------

    def _money_back_guarantee(self, ctx: AgentContext) -> None:
        now = utcnow()
        rows = ctx.db.execute(
            select(PageTest, Payment)
            .join(Payment, Payment.test_id == PageTest.id)
            .where(
                PageTest.kind == TestKind.customer,
                PageTest.status.in_([TestStatus.delivered, *STUCK]),
                Payment.status == PaymentStatus.succeeded,
            )
            .order_by(Payment.id)
        ).all()
        for test, payment in rows:
            if test.status == TestStatus.refunded:  # second payment for a test refunded this run
                continue
            why = self._refund_reason(test, payment, now)
            if why:
                self._refund(ctx, test, payment, why)
        self._maybe_summarize(ctx, now)

    def _refund_reason(self, test: PageTest, payment: Payment, now) -> str | None:
        if test.status == TestStatus.delivered:
            results = test.results or {}
            if results.get("winner") == Winner.rewrite:
                return None
            outcome = "tied with" if results.get("winner") == Winner.tie else "lost to"
            summary = results.get("summary") or "no summary"
            return f"Our rewrite {outcome} the original ({summary}), so the guarantee applies."
        if now - payment.created_at > STUCK_AFTER:
            hours = (now - payment.created_at).total_seconds() / 3600
            return f"The test has been '{test.status}' for {hours:.1f} hours after payment; refunding."
        return None

    def _refund(self, ctx: AgentContext, test: PageTest, payment: Payment, why: str) -> bool:
        amount = payment.amount
        verdict = ctx.check(
            OutboundKind.refund, f"Refund ${amount:.2f}: {why}", amount=amount, amount_paid=payment.amount
        )
        if not verdict:
            ctx.log(
                "refund_blocked",
                f"Compliance blocked the refund ({verdict.reason}); will retry.",
                test_id=test.public_id,
                amount=amount,
            )
            return False
        try:
            ok = whop.refund(payment.whop_payment_id, amount)
        except Exception as e:  # network trouble: retry on the next run
            ctx.log(
                "refund_failed",
                f"Whop refund errored ({type(e).__name__}); will retry.",
                test_id=test.public_id,
                amount=amount,
            )
            return False
        if not ok:
            ctx.log(
                "refund_failed", "Whop refused the refund; will retry.", test_id=test.public_id, amount=amount
            )
            return False

        payment.status = PaymentStatus.refunded
        test.status = TestStatus.refunded
        ctx.db.flush()
        ctx.log("refunded", why, test_id=test.public_id, amount=amount)
        self._email_customer(ctx, test, amount, why)
        return True

    def _email_customer(self, ctx: AgentContext, test: PageTest, amount: float, why: str) -> None:
        customer = ctx.db.get(Customer, test.customer_id) if test.customer_id else None
        if customer is None:
            return
        report = f"{settings.public_web_url}/report/{test.public_id}"
        body = (
            f"<p>Hi,</p><p>We promised a refund if our rewrite of your landing page didn't beat yours. "
            f"{html.escape(why)}</p>"
            f"<p>We've refunded your ${amount:.2f} through Whop. It usually shows up in 5&ndash;10 business days.</p>"
            f'<p>Your report: <a href="{report}">{report}</a></p><p>&mdash; FirstGlance</p>'
        )
        if ctx.check(OutboundKind.email, body):
            notify.send_email(customer.email, "Your FirstGlance refund", body)

    def _maybe_summarize(self, ctx: AgentContext, now) -> None:
        last = ctx.db.scalar(
            select(func.max(DecisionLog.created_at)).where(
                DecisionLog.agent == AgentName.finance, DecisionLog.action == "books_checked"
            )
        )
        if last and now - last < SUMMARY_EVERY:
            return

        def total(status: PaymentStatus) -> float:
            return float(
                ctx.db.scalar(
                    select(func.coalesce(func.sum(Payment.amount), 0.0)).where(Payment.status == status)
                )
            )

        kept, refunded = total(PaymentStatus.succeeded), total(PaymentStatus.refunded)
        ctx.log(
            "books_checked",
            f"${kept:.2f} kept, ${refunded:.2f} refunded under the money-back guarantee.",
            revenue_usd=round(kept, 2),
            refunded_usd=round(refunded, 2),
        )
