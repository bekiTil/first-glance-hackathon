"""Bereket's parts: intake, tests routes, Tester agent, guardrails, Company Log + stats."""

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.agents import intake, tester
from app.agents.base import AgentContext
from app.agents.tester import TesterAgent
from app.config import settings
from app.db import SessionLocal, init_db, session_scope
from app.db_time import utcnow
from app.enums import AgentName, Arm, OutboundKind, StateKey, TestKind, TestStatus, Winner
from app.integrations import notify, terac
from app.main import app
from app.models import DecisionLog, PageTest, TestAnswer
from app.schemas import HeroCopy
from app.worker import run_agent

HTML = """<html><head><title>Acme | Synergy</title><meta name="description" content="Meta description fallback text">
</head><body><nav><a class="btn" href="/login">Log in</a></nav>
<header><h1>Synergy at <span>scale</span></h1>
<p>Unlock the power of your team with next-gen orchestration.</p>
<a class="btn btn-primary" href="/start">Start free trial</a></header>
<script>var hero = "not this";</script><footer><p>Copyright Acme Inc, all rights reserved forever.</p></footer>
</body></html>"""

ORIGINAL = HeroCopy(headline="Synergy at scale", subhead="Next-gen orchestration.", cta="Start free trial")


@pytest.fixture
def db():
    """A session that is rolled back, so guardrail tests leave no state behind."""
    init_db()
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def no_network(monkeypatch):
    monkeypatch.setattr(intake, "read_hero", lambda url: ORIGINAL)


def _make(db, *, status=TestStatus.paid, kind=TestKind.customer, what="Payroll software for dental clinics"):
    test = PageTest(
        kind=kind,
        url="https://acme.example",
        what_you_do=what,
        original=ORIGINAL.model_dump(),
        rewrite=HeroCopy(headline="Payroll software for dental clinics").model_dump(),
        status=status,
        price_paid=15.0,
    )
    db.add(test)
    db.flush()
    return test


def _answers(db, test, arm, texts, signup=3):
    for i, text in enumerate(texts):
        db.add(TestAnswer(test_id=test.id, participant_ref=f"{arm}-{i}", arm=arm, answer=text, signup=signup))


# ---------- intake ----------


def test_parse_hero_from_html():
    hero = intake._parse(HTML).guess()
    assert hero == HeroCopy(
        headline="Synergy at scale",
        subhead="Unlock the power of your team with next-gen orchestration.",
        cta="Start free trial",
    )


def test_parse_falls_back_to_meta_when_no_h1():
    page = intake._parse(
        '<title>Acme</title><meta property="og:title" content="Acme payroll"><div id=root></div>'
    )
    assert page.needs_js() and page.guess().headline == "Acme payroll"


@pytest.mark.parametrize(
    "url", ["http://localhost:8000", "http://127.0.0.1/x", "http://10.0.0.5", "not a url"]
)
def test_read_hero_refuses_private_or_bad_urls(url):
    with pytest.raises(ValueError):
        intake.read_hero(url)


def test_rewrite_mock_leads_with_founder_sentence():
    rewrite = intake.write_rewrite(ORIGINAL, "payroll software for dental clinics.")
    assert rewrite.headline == "Payroll software for dental clinics" and rewrite.cta == "Start free trial"


# ---------- routes ----------


def test_create_get_confirm(no_network):
    with TestClient(app) as client:
        r = client.post(
            "/api/tests",
            json={
                "url": "acme.example",
                "what_you_do": "Payroll for dentists",
                "email": "Founder@Acme.example",
            },
        )
        assert r.status_code == 200, r.text
        t = r.json()
        assert t["status"] == "draft" and t["url"] == "https://acme.example"
        assert t["original"]["headline"] == "Synergy at scale" and t["rewrite"]["headline"]
        assert t["responses_so_far"] == 0 and t["results"] is None and t["price_usd"] > 0

        assert client.get(f"/api/tests/{t['id']}").json()["id"] == t["id"]
        assert client.get("/api/tests/nope").status_code == 404
        checkout = client.post(f"/api/tests/{t['id']}/confirm").json()["checkout_url"]
        assert f"/api/dev/fake-pay/{t['id']}" in checkout
        assert client.get(f"/api/tests/{t['id']}").json()["status"] == "awaiting_payment"

        log = client.get("/api/company/log?agent=tester").json()
        assert any(e["action"] == "read_page" and e["data"]["test_id"] == t["id"] for e in log)
        assert "founder@acme.example" not in str(client.get("/api/company/log").json()).lower()


def test_create_unreadable_page_is_422(monkeypatch):
    def boom(url):
        raise ValueError("couldn't read that page")

    monkeypatch.setattr(intake, "read_hero", boom)
    with TestClient(app) as client:
        r = client.post(
            "/api/tests", json={"url": "https://x.example", "what_you_do": "stuff here", "email": "a@b.co"}
        )
        assert r.status_code == 422


def test_confirm_refused_after_payment():
    with TestClient(app) as client:
        with session_scope() as s:
            pid = _make(s, status=TestStatus.testing).public_id
        assert client.post(f"/api/tests/{pid}/confirm").status_code == 409


# ---------- Tester ----------


def test_tester_launches_grades_and_delivers():
    with session_scope() as s:
        test = _make(s)
        from app.models import Customer

        c = Customer(email="dentist-founder@example.com")
        s.add(c)
        s.flush()
        test.customer_id = c.id
        pid = test.public_id

    run_agent(TesterAgent())
    with session_scope() as s:
        test = s.scalar(select(PageTest).where(PageTest.public_id == pid))
        assert test.status == TestStatus.testing and test.terac_id and test.launched_at
        _answers(
            s, test, Arm.original, ["no idea", "some AI thing", "orchestration for teams", "a dental clinic"]
        )
        _answers(s, test, Arm.rewrite, ["payroll for dentists"] * 3 + ["accounting thing"], signup=4)

    notify.OUTBOX.clear()
    run_agent(TesterAgent())
    with session_scope() as s:
        test = s.scalar(select(PageTest).where(PageTest.public_id == pid))
        assert test.status == TestStatus.delivered and test.delivered_at
        r = test.results
        assert r["winner"] == Winner.rewrite and r["rewrite"]["understood"] == 3
        assert r["summary"] == "1/4 understood yours, 3/4 understood ours."
        assert r["rewrite"]["avg_signup"] == 4.0 and len(r["original"]["sample_answers"]) == 4
        graded = s.scalars(select(TestAnswer).where(TestAnswer.test_id == test.id)).all()
        assert all(a.understood is not None for a in graded)
    assert any(f"/report/{pid}" in m["body"] for m in notify.OUTBOX)

    with TestClient(app) as client:
        out = client.get(f"/api/tests/{pid}").json()
        assert out["responses_so_far"] == 8 and out["results"]["winner"] == "rewrite"
        stats = client.get("/api/company/stats").json()
        assert stats["tests_delivered"] >= 1 and stats["rewrite_win_rate"] > 0
        actions = {e["action"] for e in client.get("/api/company/log").json()}
        assert {"launched_test", "graded_test", "delivered_report"} <= actions


def test_tester_waits_for_enough_answers_then_times_out():
    with session_scope() as s:
        test = _make(s, status=TestStatus.testing, kind=TestKind.self)
        test.launched_at = utcnow()
        _answers(s, test, Arm.original, ["no idea"])
        _answers(s, test, Arm.rewrite, ["payroll software for dentists"])
        pid = test.public_id
    run_agent(TesterAgent())
    with session_scope() as s:
        test = s.scalar(select(PageTest).where(PageTest.public_id == pid))
        assert test.status == TestStatus.testing
        test.launched_at = utcnow() - timedelta(minutes=settings.test_timeout_minutes + 1)
    notify.OUTBOX.clear()
    run_agent(TesterAgent())
    with session_scope() as s:
        test = s.scalar(select(PageTest).where(PageTest.public_id == pid))
        assert test.status == TestStatus.delivered
        assert test.results["summary"] == "0/1 understood our old copy, 1/1 understood the new one."
    assert notify.OUTBOX == []  # self tests are not emailed


def test_tester_needs_https_for_real_terac(monkeypatch):
    monkeypatch.setattr(settings, "mock_terac", False)
    monkeypatch.setattr(settings, "public_web_url", "http://localhost:5173")
    monkeypatch.setattr(terac, "create_study", lambda *a, **k: pytest.fail("must not call Terac"))
    with session_scope() as s:
        pid = _make(s).public_id
    run_agent(TesterAgent())
    run_agent(TesterAgent())
    with session_scope() as s:
        assert s.scalar(select(PageTest).where(PageTest.public_id == pid)).status == TestStatus.paid
        waits = s.scalars(select(DecisionLog).where(DecisionLog.action == "waiting_for_public_url")).all()
        assert len([w for w in waits if w.data.get("test_id") == pid]) == 1


def test_tester_reuses_draft_when_unaffordable(monkeypatch):
    created, launched = [], []

    def create(**kw):
        created.append(kw)
        return {"id": "opp-9", "cost_per_participant": 1.5, "total_cost": 15.0, "affordable": False}

    monkeypatch.setattr(terac, "create_study", create)
    monkeypatch.setattr(terac, "launch", lambda opp: launched.append(opp) or "active")
    with session_scope() as s:
        pid = _make(s).public_id
    run_agent(TesterAgent())
    with session_scope() as s:
        assert s.scalar(select(PageTest).where(PageTest.public_id == pid)).status == TestStatus.paid
    run_agent(TesterAgent())  # balance topped up: launch the same draft
    with session_scope() as s:
        assert s.scalar(select(PageTest).where(PageTest.public_id == pid)).status == TestStatus.testing
    mine = [c for c in created if c["task_url"].endswith(f"/t/{pid}")]  # other paid tests may exist
    assert len(mine) == 1 and "opp-9" in launched


def test_results_tie_breaks_on_signup():
    def a(arm, text, signup):
        return TestAnswer(arm=arm, answer=text, signup=signup, understood=True)

    r = tester.build_results([a(Arm.original, "x", 2)], [a(Arm.rewrite, "y", 4)], TestKind.customer)
    assert r.winner == Winner.rewrite
    r = tester.build_results([a(Arm.original, "x", 3)], [a(Arm.rewrite, "y", 3)], TestKind.customer)
    assert r.winner == Winner.tie


# ---------- guardrails ----------


def test_guardrails_rules(db):
    ctx = AgentContext(db=db, agent=AgentName.growth)
    assert ctx.check(OutboundKind.email, "<p>Your results</p>")
    assert not ctx.check(OutboundKind.email, "  ")
    assert not ctx.check(OutboundKind.post, "Guaranteed 30% more signups with FirstGlance!")
    assert not ctx.check(OutboundKind.post, "We will boost your conversions by 40% overnight")
    assert ctx.check(
        OutboundKind.post, "AI agents test your page with real people. Money-back guarantee if ours loses."
    )
    assert not ctx.check(OutboundKind.sms, "hi", sms_consent=True, phone_verified=False)
    assert not ctx.check(OutboundKind.refund, amount=20, amount_paid=15)
    assert ctx.check(OutboundKind.refund, amount=15, amount_paid=15)
    blocks = db.scalars(select(DecisionLog).where(DecisionLog.agent == AgentName.compliance)).all()
    assert len(blocks) >= 5 and all(b.data["requested_by"] == "growth" for b in blocks)


def test_guardrails_price_cooldown_and_ad_budget(db):
    ctx = AgentContext(db=db, agent=AgentName.ceo)
    assert not ctx.check(OutboundKind.price_change, new_price=50)
    assert ctx.check(OutboundKind.price_change, new_price=19)
    ctx.log("price_changed", "test", old=15, new=19)
    assert not ctx.check(OutboundKind.price_change, new_price=19)

    growth = AgentContext(db=db, agent=AgentName.growth)
    assert growth.check(OutboundKind.ad, "Sponsored: AI-run 5-second tests", budget_usd=15)
    assert not growth.check(OutboundKind.ad, "Sponsored: AI-run 5-second tests", budget_usd=10)
    assert growth.get_state(StateKey.ad_spend_today)["usd"] == 15


def test_kill_switch_blocks_everything(db):
    ctx = AgentContext(db=db, agent=AgentName.ceo)
    ctx.set_state(StateKey.kill_switch, True)
    assert not ctx.check(OutboundKind.email, "<p>hello</p>")
    assert not ctx.check(OutboundKind.price_change, new_price=15)
