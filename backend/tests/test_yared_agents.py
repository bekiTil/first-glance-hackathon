"""Yared's part: CEO + Growth agents (Research, test page and landing copy: add tests as you build)."""

from sqlalchemy import select

from app.agents.base import AgentContext
from app.agents.ceo import CeoAgent
from app.agents.growth import GrowthAgent
from app.db import init_db, session_scope
from app.enums import AgentName, StateKey
from app.models import DecisionLog
from app.schemas import Stats


def _run(agent):
    with session_scope() as db:
        agent.run(AgentContext(db=db, agent=agent.name))


def test_growth_publishes_on_site():
    init_db()
    _run(GrowthAgent())
    with session_scope() as db:
        entry = db.scalars(select(DecisionLog).where(DecisionLog.action == "published_post")).first()
        assert entry and "/test/new" in entry.data["post"] and entry.data["channel"] == "site"


def test_ceo_sets_priorities(monkeypatch):
    init_db()
    fake = Stats(
        revenue_usd=30,
        payments=2,
        refunds=0,
        tests_created=5,
        tests_paid=2,
        tests_delivered=1,
        rewrite_win_rate=1.0,
        conversion_rate=0.4,
        price_usd=15,
    )
    monkeypatch.setattr("app.agents.ceo.compute_stats", lambda db: fake)
    _run(CeoAgent())
    with session_scope() as db:
        ctx = AgentContext(db=db, agent=AgentName.ceo)
        assert ctx.get_state(StateKey.priorities) and ctx.get_state(StateKey.target_audiences)
        assert db.scalars(select(DecisionLog).where(DecisionLog.action == "hourly_report")).first()


# ---------- test page + research self-test ----------

from fastapi.testclient import TestClient  # noqa: E402

from app.agents.research import DEFAULT_LANDING, ResearchAgent  # noqa: E402
from app.enums import JobType, TestKind, TestStatus  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Job, PageTest, TestAnswer  # noqa: E402
from app.schemas import ArmResult, HeroCopy, TestResults  # noqa: E402


def _page_test(status=TestStatus.testing, kind=TestKind.customer) -> str:
    with session_scope() as db:
        t = PageTest(
            kind=kind,
            url="https://example.com",
            what_you_do="Payroll for dentists",
            status=status,
            original=HeroCopy(headline="Synergy at scale").model_dump(),
            rewrite=HeroCopy(headline="Payroll for dental clinics").model_dump(),
        )
        db.add(t)
        db.flush()
        return t.public_id


def test_test_page_balances_arms_and_records_answers():
    init_db()
    tid = _page_test()
    with TestClient(app) as client:
        arms = []
        for i in range(6):
            page = client.get(f"/api/t/{tid}?participant=p{i}").json()
            assert page["seconds"] == 5 and page["hero"]["headline"]
            arms.append(page["arm"])
            body = {"participant_ref": f"p{i}", "arm": page["arm"], "answer": "payroll", "signup": 4}
            assert client.post(f"/api/t/{tid}/answers", json=body).json()["ok"]
        assert arms.count("original") == 3 and arms.count("rewrite") == 3
        # same participant keeps their arm; duplicate answer is ignored
        assert client.get(f"/api/t/{tid}?participant=p0").json()["arm"] == arms[0]
        dup = {"participant_ref": "p0", "arm": arms[0], "answer": "x", "signup": 1}
        assert "Already" in client.post(f"/api/t/{tid}/answers", json=dup).json()["message"]
    with session_scope() as db:
        test = db.query(PageTest).filter(PageTest.public_id == tid).one()
        assert db.query(TestAnswer).filter(TestAnswer.test_id == test.id).count() == 6


def test_test_page_closed_when_not_testing():
    init_db()
    tid = _page_test(status=TestStatus.delivered)
    with TestClient(app) as client:
        assert client.get(f"/api/t/{tid}").status_code == 409
        body = {"arm": "original", "answer": "x", "signup": 3}
        assert client.post(f"/api/t/{tid}/answers", json=body).json()["ok"] is False


def test_research_self_test_start_and_adopt():
    init_db()
    with TestClient(app) as client:
        assert client.get("/api/landing-copy").json()["headline"]
        _run(ResearchAgent())  # starts round 1 + queues run_test for the Tester
        with session_scope() as db:
            test = (
                db.query(PageTest).filter(PageTest.kind == TestKind.self).order_by(PageTest.id.desc()).first()
            )
            assert test.status == TestStatus.paid and test.original["headline"] and test.rewrite["headline"]
            job = db.query(Job).filter(Job.type == JobType.run_test).order_by(Job.id.desc()).first()
            assert job.payload["test_id"] == test.public_id
            # pretend the Tester delivered it and the rewrite won
            test.status = TestStatus.delivered
            test.results = TestResults(
                original=ArmResult(responses=5, understood=2, understood_rate=0.4, avg_signup=2.8),
                rewrite=ArmResult(responses=5, understood=5, understood_rate=1.0, avg_signup=3.9),
                winner="rewrite",
                summary="2/5 understood ours before, 5/5 after",
            ).model_dump()
            new_headline = test.rewrite["headline"]
        _run(ResearchAgent())  # adopts the winner
        assert client.get("/api/landing-copy").json()["headline"] == new_headline != DEFAULT_LANDING.headline
        selftest = client.get("/api/self-test").json()
        assert selftest["status"] == "delivered" and selftest["results"]["winner"] == "rewrite"
    with session_scope() as db:
        entry = db.scalars(select(DecisionLog).where(DecisionLog.action == "before_after")).first()
        assert entry and entry.data["adopted"] and entry.data["understood_after"] == 1.0
