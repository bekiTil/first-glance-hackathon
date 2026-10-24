"""Natnael's part: Whop, payment webhook, contact form, Finance + Support agents."""

import base64
import hashlib
import hmac
import json
import time
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.agents.base import AgentContext
from app.agents.finance import FinanceAgent
from app.agents.support import SupportAgent
from app.config import settings
from app.db import session_scope
from app.db_time import utcnow
from app.enums import AgentName, JobType, PaymentStatus, TestStatus, Winner
from app.integrations import notify, whop
from app.main import app
from app.models import Customer, DecisionLog, Job, PageTest, Payment
from app.schemas import HeroCopy, PaymentEvent, SupportRequest


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def make_test(email: str, status=TestStatus.draft, winner: Winner | None = None) -> str:
    with session_scope() as db:
        customer = Customer(email=email)
        db.add(customer)
        db.flush()
        test = PageTest(
            customer_id=customer.id,
            url="https://example.com",
            what_you_do="Payroll for dentists",
            original=HeroCopy(headline="Synergy at scale").model_dump(),
            rewrite=HeroCopy(headline="Payroll software for dental clinics").model_dump(),
            status=status,
        )
        if winner:
            test.results = {"winner": winner, "summary": "3/5 understood yours, 2/5 understood ours"}
        db.add(test)
        db.flush()
        return test.public_id


def add_payment(public_id: str, paid_hours_ago: float = 0) -> str:
    with session_scope() as db:
        test = db.scalar(select(PageTest).where(PageTest.public_id == public_id))
        db.add(
            Payment(
                whop_payment_id=f"pay-{public_id}",
                test_id=test.id,
                amount=15.0,
                created_at=utcnow() - timedelta(hours=paid_hours_ago),
            )
        )
    return f"pay-{public_id}"


def run(agent, job_type=None, payload=None):
    with session_scope() as db:
        job = Job(type=job_type, payload=payload) if job_type else None
        agent.run(AgentContext(db=db, agent=agent.name), job)


def status_of(public_id: str) -> str:
    with session_scope() as db:
        return db.scalar(select(PageTest.status).where(PageTest.public_id == public_id))


def last_log(agent: AgentName) -> DecisionLog:
    with session_scope() as db:
        return db.scalars(
            select(DecisionLog).where(DecisionLog.agent == agent).order_by(DecisionLog.id.desc())
        ).first()


# ---------- routes ----------


def test_whop_webhook_queues_payment(client):
    event = PaymentEvent(whop_payment_id="pay_hook", test_public_id="t1", amount=15.0)
    assert client.post("/api/webhooks/whop", content=event.model_dump_json()).json()["ok"]
    with session_scope() as db:
        job = db.scalars(
            select(Job).where(Job.type == JobType.payment_received).order_by(Job.id.desc())
        ).first()
        assert job.payload["whop_payment_id"] == "pay_hook"


def test_contact_form_queues_support(client):
    r = client.post("/api/support", json={"email": "a@b.co", "message": "how long does it take?"})
    assert r.status_code == 200 and r.json()["ok"]
    with session_scope() as db:
        job = db.scalars(
            select(Job).where(Job.type == JobType.support_message).order_by(Job.id.desc())
        ).first()
        assert SupportRequest.model_validate(job.payload).message == "how long does it take?"


def test_whop_signature(monkeypatch):
    monkeypatch.setattr(settings, "mock_whop", False)
    monkeypatch.setattr(settings, "whop_webhook_secret", "ws_test_secret")
    body = json.dumps(
        {
            "type": "payment.succeeded",
            "data": {
                "id": "pay_123",
                "user": {"id": "user_1"},
                "customer_email": "a@b.co",
                "metadata": {"test_public_id": "abc"},
                "total": {"amount": "15.00", "currency": "usd"},
                "currency": "usd",
            },
        }
    ).encode()
    ts = str(int(time.time()))
    sig = base64.b64encode(hmac.new(b"ws_test_secret", f"m1.{ts}.".encode() + body, hashlib.sha256).digest())
    headers = {"Webhook-Id": "m1", "Webhook-Timestamp": ts, "Webhook-Signature": f"v1,{sig.decode()}"}
    assert whop.parse_webhook(body, headers) == PaymentEvent(
        whop_payment_id="pay_123", whop_user_id="user_1", email="a@b.co", test_public_id="abc", amount=15.0
    )
    with pytest.raises(ValueError):
        whop.parse_webhook(body + b" ", headers)
    with pytest.raises(ValueError):
        whop.parse_webhook(body, {**headers, "Webhook-Timestamp": str(int(time.time()) - 3600)})
    other = json.dumps({"type": "membership.went_valid", "data": {}}).encode()
    sig = base64.b64encode(hmac.new(b"ws_test_secret", f"m2.{ts}.".encode() + other, hashlib.sha256).digest())
    assert (
        whop.parse_webhook(other, {**headers, "Webhook-Id": "m2", "Webhook-Signature": f"v1,{sig.decode()}"})
        is None
    )


# ---------- Finance ----------


def test_finance_records_payment_once_and_starts_test():
    tid = make_test("pay@example.com", status=TestStatus.awaiting_payment)
    payload = PaymentEvent(
        whop_payment_id=f"p-{tid}", whop_user_id=f"u-{tid}", test_public_id=tid, amount=15.0
    )
    run(FinanceAgent(), JobType.payment_received, payload.model_dump(mode="json"))
    run(FinanceAgent(), JobType.payment_received, payload.model_dump(mode="json"))
    assert status_of(tid) == TestStatus.paid
    with session_scope() as db:
        test = db.scalar(select(PageTest).where(PageTest.public_id == tid))
        assert test.price_paid == 15.0
        assert db.query(Payment).filter(Payment.test_id == test.id).count() == 1
        assert db.get(Customer, test.customer_id).whop_user_id == f"u-{tid}"
        run_jobs = db.scalars(select(Job).where(Job.type == JobType.run_test)).all()
        assert [j.payload for j in run_jobs].count({"test_id": tid}) == 1


def test_finance_matches_by_email_without_metadata():
    tid = make_test("nometa@example.com", status=TestStatus.awaiting_payment)
    payload = PaymentEvent(
        whop_payment_id=f"p-{tid}", email="NoMeta@example.com", test_public_id="", amount=15.0
    )
    run(FinanceAgent(), JobType.payment_received, payload.model_dump(mode="json"))
    assert status_of(tid) == TestStatus.paid


def test_money_back_guarantee():
    lost = make_test("lost@example.com", TestStatus.delivered, Winner.original)
    tied = make_test("tied@example.com", TestStatus.delivered, Winner.tie)
    won = make_test("won@example.com", TestStatus.delivered, Winner.rewrite)
    stuck = make_test("stuck@example.com", TestStatus.testing)
    fresh = make_test("fresh@example.com", TestStatus.testing)
    for tid in (lost, tied, won, fresh):
        add_payment(tid)
    stuck_payment = add_payment(stuck, paid_hours_ago=4)

    notify.OUTBOX.clear()
    run(FinanceAgent())
    assert [status_of(t) for t in (lost, tied, won, stuck, fresh)] == [
        TestStatus.refunded,
        TestStatus.refunded,
        TestStatus.delivered,
        TestStatus.refunded,
        TestStatus.testing,
    ]
    with session_scope() as db:
        assert db.scalar(select(Payment.status).where(Payment.whop_payment_id == stuck_payment)) == (
            PaymentStatus.refunded
        )
        refunds = db.scalars(select(DecisionLog).where(DecisionLog.action == "refunded")).all()
        assert all("@" not in json.dumps(e.data) for e in refunds)
    assert {m["to"] for m in notify.OUTBOX} == {"lost@example.com", "tied@example.com", "stuck@example.com"}

    run(FinanceAgent())  # already refunded: nothing happens twice
    with session_scope() as db:
        assert db.query(DecisionLog).filter(DecisionLog.action == "refunded").count() == 3


# ---------- Support ----------


def test_support_answers_by_email_and_explains_refunds():
    tid = make_test("asker@example.com", TestStatus.testing)
    notify.OUTBOX.clear()
    message = "Where is my report? I want a refund. Call me at 212-555-0100"
    run(
        SupportAgent(),
        JobType.support_message,
        {"email": "asker@example.com", "message": message, "test_id": tid},
    )
    assert notify.OUTBOX[-1]["to"] == "asker@example.com"
    assert f"/report/{tid}" in notify.OUTBOX[-1]["body"] and "automatically" in notify.OUTBOX[-1]["body"]
    entry = last_log(AgentName.support)
    assert entry.action == "answered_customer" and entry.data["refund_request"] is True
    assert "555" not in json.dumps(entry.data) and "@" not in json.dumps(entry.data)
    assert status_of(tid) == TestStatus.testing  # Support never refunds


def test_support_hides_other_peoples_tests():
    tid = make_test("owner@example.com", TestStatus.delivered, Winner.rewrite)
    notify.OUTBOX.clear()
    run(
        SupportAgent(),
        JobType.support_message,
        {"email": "snoop@example.com", "message": "status?", "test_id": tid},
    )
    assert tid not in notify.OUTBOX[-1]["body"]
    assert last_log(AgentName.support).data["test_id"] is None
