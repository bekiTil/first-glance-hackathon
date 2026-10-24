"""Shared contracts and mock plumbing. These must pass before anything is merged to main."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.agents import ALL_AGENTS
from app.agents.base import AgentContext
from app.config import settings
from app.db import init_db, session_scope
from app.db_time import utcnow
from app.enums import AgentName, JobStatus, JobType, StateKey
from app.integrations import exa, llm, notify, solari, terac, whop
from app.main import app
from app.models import Customer, DecisionLog, Job, PageTest, TestAnswer
from app.schemas import HeroCopy, PaymentEvent
from app.worker import run_once


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
    assert JobType.run_test in by_name[AgentName.tester].handles
    assert JobType.payment_received in by_name[AgentName.finance].handles
    assert JobType.support_message in by_name[AgentName.support].handles


def test_mocks_return_contract_types():
    assert solari.screenshot("https://example.com", settings.data_dir / "x.png") is None
    assert "/api/dev/fake-pay/abc" in whop.create_checkout("abc", "a@b.co", 15.0)
    pay = PaymentEvent(whop_payment_id="p1", test_public_id="abc", amount=15.0)
    assert whop.parse_webhook(pay.model_dump_json().encode(), {}) == pay
    notify.send_email("a@b.co", "hi", "<p>hi</p>")
    assert notify.OUTBOX[-1]["channel"] == "email"
    assert exa.search("landing pages", n=1)
    quote = terac.create_study("t", "d", "https://example.com/t/x", 10, 2)
    assert quote["id"] and terac.launch(quote["id"]) == "active"
    assert llm.ask_json("s", "p", {}, mock={"x": 1}) == {"x": 1}


def test_context_state_and_log():
    init_db()
    with session_scope() as db:
        ctx = AgentContext(db=db, agent=AgentName.ceo)
        ctx.set_state(StateKey.price_usd, 12.0)
        assert ctx.get_state(StateKey.price_usd) == 12.0
        entry = ctx.log("test_action", "because", n=1)
        assert entry.id and entry.agent == AgentName.ceo


def _make_test(db) -> PageTest:
    customer = Customer(email="founder@example.com")
    db.add(customer)
    db.flush()
    test = PageTest(
        customer_id=customer.id,
        url="https://example.com",
        what_you_do="Payroll for dentists",
        original=HeroCopy(headline="Synergy at scale").model_dump(),
        rewrite=HeroCopy(headline="Payroll software for dental clinics").model_dump(),
    )
    db.add(test)
    db.flush()
    return test


def test_dev_fake_pay_and_fake_answers():
    with TestClient(app) as client:
        with session_scope() as db:
            public_id = _make_test(db).public_id
        assert client.get(f"/api/dev/fake-pay/{public_id}", follow_redirects=False).status_code == 302
        assert client.post(f"/api/dev/fake-answers/{public_id}?n=6").status_code == 200
        with session_scope() as db:
            job = db.query(Job).filter(Job.type == JobType.payment_received).order_by(Job.id.desc()).first()
            assert PaymentEvent.model_validate(job.payload).test_public_id == public_id
            test = db.query(PageTest).filter(PageTest.public_id == public_id).one()
            assert db.query(TestAnswer).filter(TestAnswer.test_id == test.id).count() == 6


def test_worker_survives_unimplemented_agents():
    started = utcnow()
    run_once()  # must not raise
    with session_scope() as db:
        errors = db.query(DecisionLog).filter(
            DecisionLog.action == "error", DecisionLog.created_at >= started
        )
        assert errors.count() == 0
        assert db.query(Job).filter(Job.status == JobStatus.running).count() == 0
