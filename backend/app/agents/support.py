"""Sales & support agent. Owner: Natnael.

- Consumes support_message jobs (payload = schemas.SupportRequest from the contact form).
- Answers with llm.ask_text: what FirstGlance is, how long it takes, where their report is
  ({PUBLIC_WEB_URL}/report/<test_id> if given). Test details are only shared when the test belongs
  to the email that wrote in. Never promises things we don't do.
- Sends with notify.send_email only if ctx.check(OutboundKind.email, answer) allows.
- Refund requests: explains the automatic guarantee; never refunds here (Finance decides from records).
- ctx.log("answered_customer", ...) without the customer's email in data.
"""

import html
import re

from sqlalchemy import func, select

from app.agents.base import Agent, AgentContext
from app.config import settings
from app.enums import AgentName, JobType, OutboundKind, StateKey
from app.integrations import llm, notify
from app.models import Customer, Job, PageTest, Payment, TestAnswer
from app.schemas import SupportRequest

SYSTEM = """You are the support agent of FirstGlance, a small company run entirely by AI agents.
What we sell: for ${price:.0f}, about 10 real people (recruited through Terac) each see ONE version of a
startup's landing page hero for 10 seconds: either the founder's original or a clearer rewrite written by
Claude. Each answers "What does this company do?" and "How likely are you to sign up? (1-5)". Claude
grades the answers and the founder gets a report with both scores and the new copy. A test usually takes
30 minutes to 2 hours after payment, depending on how fast participants answer.
Money-back guarantee: if our rewrite doesn't win, or the test gets stuck for more than 3 hours, the
refund happens automatically through Whop; nobody needs to ask. You cannot issue refunds yourself.
Rules: never promise anything not listed here (no guaranteed conversion lift, no extra participants,
no discounts). Never invent numbers. If you don't know, say a person on the team will follow up.
Write a short, friendly email reply in plain text (no subject line, no markdown), signed "FirstGlance"."""

REFUND_WORDS = ("refund", "money back", "chargeback", "charge back", "cancel")


class SupportAgent(Agent):
    name = AgentName.support
    handles = (JobType.support_message,)

    def run(self, ctx: AgentContext, job: Job | None = None) -> None:
        if job is None:
            return
        request = SupportRequest.model_validate(job.payload)
        test = self._own_test(ctx, request)
        asks_refund = any(w in request.message.lower() for w in REFUND_WORDS)
        price = float(ctx.get_state(StateKey.price_usd, settings.starting_price_usd))

        answer = llm.ask_text(
            SYSTEM.format(price=price),
            f"Facts about their test:\n{self._facts(ctx, request, test)}\n\n"
            f"Customer's message:\n{request.message[:4000]}",
            mock=_mock_answer(test, asks_refund, price),
        ).strip()

        body = "".join(f"<p>{html.escape(p)}</p>" for p in answer.split("\n\n") if p.strip())
        sent = bool(ctx.check(OutboundKind.email, answer))
        if sent:
            notify.send_email(request.email, "Re: your FirstGlance question", body)
        ctx.log(
            "answered_customer" if sent else "answer_blocked",
            ("Answered a customer by email." if sent else "Drafted an answer but compliance blocked it.")
            + (" They asked about a refund; explained the automatic guarantee." if asks_refund else ""),
            test_id=test.public_id if test else None,
            refund_request=asks_refund,
            question=_redact(request.message[:200]),
            answer=_redact(answer[:500]),
        )

    def _own_test(self, ctx: AgentContext, request: SupportRequest) -> PageTest | None:
        """The test they mention, or their newest one, only if it belongs to the email that wrote in."""
        query = (
            select(PageTest)
            .join(Customer, Customer.id == PageTest.customer_id)
            .where(func.lower(Customer.email) == request.email.lower())
        )
        if request.test_id:
            query = query.where(PageTest.public_id == request.test_id)
        return ctx.db.scalar(query.order_by(PageTest.created_at.desc()).limit(1))

    def _facts(self, ctx: AgentContext, request: SupportRequest, test: PageTest | None) -> str:
        if test is None:
            if request.test_id:
                return (
                    "- They mentioned a test id that isn't linked to their email; share no details about it."
                )
            return "- We have no test on record for this email."
        answers = ctx.db.scalar(
            select(func.count()).select_from(TestAnswer).where(TestAnswer.test_id == test.id)
        )
        payment = ctx.db.scalar(select(Payment).where(Payment.test_id == test.id).order_by(Payment.id.desc()))
        facts = [
            f"- Page: {test.url}",
            f"- Status: {test.status}",
            f"- Answers so far: {answers}",
            f"- Report link: {settings.public_web_url}/report/{test.public_id}",
            f"- Payment: {f'${payment.amount:.2f}, {payment.status}' if payment else 'not paid yet'}",
        ]
        if test.results:
            facts.append(
                f"- Result: {test.results.get('summary', '')} (winner: {test.results.get('winner')})"
            )
        return "\n".join(facts)


def _mock_answer(test: PageTest | None, asks_refund: bool, price: float) -> str:
    lines = [
        "Hi, thanks for writing in!",
        f"For ${price:.0f}, about 10 real people each see your landing page (or our clearer rewrite) for 5 "
        "seconds and tell us what they think you do. You get a report with both scores and the new copy, "
        "usually within 2 hours of paying.",
    ]
    if test is not None:
        lines.append(
            f"Your test is currently {test.status}. Your report lives here: "
            f"{settings.public_web_url}/report/{test.public_id}"
        )
    if asks_refund:
        lines.append(
            "About refunds: if our rewrite doesn't beat your original, or the test is stuck for more than "
            "3 hours, we refund you automatically through Whop. There's nothing you need to do."
        )
    lines.append("FirstGlance")
    return "\n\n".join(lines)


def _redact(text: str) -> str:
    """The Company Log is public: strip emails and phone numbers out of anything customers wrote."""
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[email]", text)
    return re.sub(r"\+?\d[\d\s().-]{7,}\d", "[phone]", text)
