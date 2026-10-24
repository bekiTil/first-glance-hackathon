"""Registry of every agent the worker runs. Compliance lives in guardrails.py (called by all)."""

from app.agents.base import Agent
from app.agents.ceo import CeoAgent
from app.agents.finance import FinanceAgent
from app.agents.growth import GrowthAgent
from app.agents.research import ResearchAgent
from app.agents.support import SupportAgent
from app.agents.tester import TesterAgent

ALL_AGENTS: list[Agent] = [
    TesterAgent(),
    FinanceAgent(),
    SupportAgent(),
    CeoAgent(),
    GrowthAgent(),
    ResearchAgent(),
]
