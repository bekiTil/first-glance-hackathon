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
