"""Yared's part: Research (Terac studies), Growth, CEO, study page API, free events."""

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.agents.base import AgentContext
from app.agents.ceo import CeoAgent
from app.agents.growth import GrowthAgent
from app.agents.research import ResearchAgent
from app.agents.study_design import ROUNDS, V1_WEIGHTS, agreement, fit_weights
from app.db import init_db, session_scope
from app.enums import AgentName, StateKey, StudyStatus
from app.main import app
from app.models import DecisionLog, Study, StudyAnswer
from app.schemas import Stats


def _run(agent):
    with session_scope() as db:
        agent.run(AgentContext(db=db, agent=agent.name))


def _actions(agent: AgentName) -> list[str]:
    with session_scope() as db:
        return [d.action for d in db.scalars(select(DecisionLog).where(DecisionLog.agent == agent))]


def test_fit_weights_learns_from_people():
    # everyone picks the lower-level option in every round-1 set
    picks = [
        (i, next(o.label for o in s.options if o.lower_level))
        for i, s in enumerate(ROUNDS[1])
        for _ in range(3)
    ]
    weights = fit_weights(ROUNDS[1], picks)
    assert weights["lower_level"] > 0
    assert agreement(ROUNDS[1], picks, weights) > agreement(ROUNDS[1], picks, V1_WEIGHTS)


def test_research_agent_full_before_after():
    init_db()
    _run(ResearchAgent())  # round 1 launched + (mock) people answer
    _run(ResearchAgent())  # learn weights + rewrite copy + launch round 2
    _run(ResearchAgent())  # measure before/after
    with session_scope() as db:
        studies = {s.round: s for s in db.scalars(select(Study))}
        assert studies[1].status == StudyStatus.completed and studies[2].status == StudyStatus.completed
        r2 = studies[2].results
        assert r2["agreement_v2"] >= r2["agreement_v1"]
        ctx = AgentContext(db=db, agent=AgentName.research)
        assert ctx.get_state(StateKey.deal_weights)["lower_level"] > 0
        assert ctx.get_state(StateKey.landing_copy)["version"] == 2
    actions = _actions(AgentName.research)
    assert {"launched_study", "updated_deal_weights", "updated_landing_copy", "before_after"} <= set(actions)


def test_study_page_api():
    init_db()
    with session_scope() as db:
        study = Study(
            kind="deal_preferences", round=1, status=StudyStatus.running, request={"public_id": "studypage1"}
        )
        db.add(study)
    with TestClient(app) as client:
        page = client.get("/api/studies/studypage1").json()
        assert len(page["sets"]) == 5 and page["landing"]["headline"]
        picks = [{"set": i, "option": "A"} for i in range(5)]
        body = {"participant_ref": "terac-sub-1", "picks": picks, "willingness": 4, "unclear": "who buys?"}
        assert client.post("/api/studies/studypage1/answers", json=body).status_code == 200
        assert "Already" in client.post("/api/studies/studypage1/answers", json=body).json()["message"]
        bad = {**body, "participant_ref": "x", "picks": picks[:2]}
        assert client.post("/api/studies/studypage1/answers", json=bad).status_code == 422
        assert client.get("/api/studies/landing-copy").json()["headline"]
    with session_scope() as db:
        assert db.query(StudyAnswer).filter(StudyAnswer.participant_ref == "terac-sub-1").count() == 1


def test_free_events_route():
    with TestClient(app) as client:
        events = client.get("/api/free-events?when=tonight").json()
        assert events and events[0]["url"]


def test_growth_publishes_on_site():
    init_db()
    _run(GrowthAgent())
    with session_scope() as db:
        entry = db.scalars(select(DecisionLog).where(DecisionLog.action == "published_post")).first()
        assert entry and "/watch/new" in entry.data["post"] and entry.data["channel"] == "site"


def test_ceo_sets_priorities(monkeypatch):
    init_db()
    fake = Stats(
        revenue_usd=6,
        payments=2,
        refunds=0,
        watches_created=5,
        watches_active=2,
        alerts_sent=1,
        clicks=1,
        purchases=0,
        conversion_rate=0.4,
        price_usd=3,
    )
    monkeypatch.setattr("app.agents.ceo.compute_stats", lambda db: fake)
    _run(CeoAgent())
    with session_scope() as db:
        assert AgentContext(db=db, agent=AgentName.ceo).get_state(StateKey.priorities)
    assert "hourly_report" in _actions(AgentName.ceo)
