"""Shared contracts and mock plumbing. These must pass before anything is merged to main."""

import json
from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

from app.agents import ALL_AGENTS
from app.agents.base import AgentContext
from app.agents.deal_score import DEFAULT_WEIGHTS
from app.config import settings
from app.db import init_db, session_scope
from app.db_time import utcnow
from app.enums import AgentName, JobStatus, JobType, StateKey
from app.integrations import exa, llm, notify, solari, terac, tickets, whop
from app.main import app
from app.models import Customer, DecisionLog, Event, Job, Watch
from app.schemas import Checklist, EventInfo, FreeEvent, Listing, PaymentEvent, Verification
from app.worker import run_once

CHECKLIST = Checklist(
    query="Knicks under $80, any Friday, 2 seats",
    performer="New York Knicks",
    date_from=date(2026, 11, 1),
    date_to=date(2026, 11, 30),
    weekdays=[4],
    max_price_per_ticket=80,
    quantity=2,
)


def test_api_matches_committed_openapi():
    """If this fails: run scripts/export_openapi.py + npm run gen:api and commit both files."""
    committed = json.loads((Path(__file__).resolve().parents[2] / "openapi.json").read_text())
    assert app.openapi()["paths"].keys() == committed["paths"].keys()
    assert app.openapi()["components"] == committed["components"]


def test_app_starts():
    with TestClient(app) as client:
        assert client.get("/api/health").json()["ok"] is True


def test_agent_registry():
    names = {a.name for a in ALL_AGENTS}
    assert names == set(AgentName) - {AgentName.compliance}  # compliance = guardrails.py
    by_name = {a.name: a for a in ALL_AGENTS}
    assert by_name[AgentName.watcher].every_minutes == settings.watch_interval_minutes
    assert JobType.payment_received in by_name[AgentName.finance].handles
    assert {JobType.email_reply, JobType.sms_received} <= set(by_name[AgentName.support].handles)


def test_mocks_return_contract_types():
    events = tickets.search_events(CHECKLIST)
    assert events and all(isinstance(e, EventInfo) and e.starts_at.weekday() == 4 for e in events)
    e = events[0]
    row = Event(
        source=e.source,
        external_id=e.external_id,
        name=e.name,
        starts_at=e.starts_at,
        venue=e.venue,
        url=e.url,
    )
    listing = tickets.best_listing(row)
    assert isinstance(listing, Listing) and listing.key
    assert isinstance(solari.verify_listing(listing, settings.data_dir / "x.png"), Verification)
    assert "/api/dev/fake-pay/abc" in whop.create_checkout("abc", "a@b.co", 3.0)
    pay = PaymentEvent(whop_payment_id="p1", watch_public_id="abc", amount=3.0)
    assert whop.parse_webhook(pay.model_dump_json().encode(), {}) == pay
    notify.send_email("a@b.co", "hi", "<p>hi</p>")
    notify.send_sms("+12125550100", "hi")
    assert [m["channel"] for m in notify.OUTBOX[-2:]] == ["email", "sms"]
    assert all(isinstance(f, FreeEvent) for f in exa.free_events())
    quote = terac.create_study("t", "d", "https://example.com/study/x", 5, 5)
    assert quote["id"] and terac.launch(quote["id"]) == "active"
    assert llm.ask_json("s", "p", {}, mock={"x": 1}) == {"x": 1}
    assert set(DEFAULT_WEIGHTS) == {"price", "lower_level", "weekend"}


def test_context_state_and_log():
    init_db()
    with session_scope() as db:
        ctx = AgentContext(db=db, agent=AgentName.ceo)
        ctx.set_state(StateKey.price_usd, 4.0)
        assert ctx.get_state(StateKey.price_usd) == 4.0
        entry = ctx.log("test_action", "because", n=1)
        assert entry.id and entry.agent == AgentName.ceo


def test_fake_pay_queues_payment_job():
    with TestClient(app) as client:
        with session_scope() as db:
            customer = Customer(email="fan@example.com")
            db.add(customer)
            db.flush()
            watch = Watch(customer_id=customer.id, query="q", checklist=CHECKLIST.model_dump(mode="json"))
            db.add(watch)
            db.flush()
            public_id = watch.public_id
        assert client.get(f"/api/dev/fake-pay/{public_id}", follow_redirects=False).status_code == 302
        with session_scope() as db:
            job = db.query(Job).filter(Job.type == JobType.payment_received).order_by(Job.id.desc()).first()
            assert PaymentEvent.model_validate(job.payload).watch_public_id == public_id


def test_worker_survives_unimplemented_agents():
    started = utcnow()
    run_once()  # must not raise
    with session_scope() as db:
        errors = db.query(DecisionLog).filter(
            DecisionLog.action == "error", DecisionLog.created_at >= started
        )
        assert errors.count() == 0
        assert db.query(Job).filter(Job.status == JobStatus.running).count() == 0
