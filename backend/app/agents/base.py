"""SHARED agent interface. Owner: Bereket.

An agent is a class with:
  name           AgentName
  every_minutes  run on a schedule (None = only when a job arrives)
  handles        JobTypes it consumes from the jobs table
  run(ctx, job)  do the work; job is None for scheduled runs

Inside run(), use:
  ctx.db                     SQLAlchemy session (committed by the worker)
  ctx.log(action, reason, **data)   -> appears on the public Company Log. Log every decision.
  ctx.get_state(key, default) / ctx.set_state(key, value)   shared company_state
  ctx.check(kind, content, **meta)  -> guardrails verdict; never send anything if not allowed
  app.integrations.llm.ask_text / ask_json / run_tools for Claude
"""

from dataclasses import dataclass
from typing import Any, ClassVar

from sqlalchemy.orm import Session

from app.enums import AgentName, JobType, OutboundKind, StateKey
from app.models import CompanyState, DecisionLog, Job


@dataclass
class AgentContext:
    db: Session
    agent: AgentName

    def log(self, action: str, reason: str, **data: Any) -> DecisionLog:
        entry = DecisionLog(agent=self.agent, action=action, reason=reason, data=data)
        self.db.add(entry)
        self.db.flush()
        return entry

    def get_state(self, key: StateKey, default: Any = None) -> Any:
        row = self.db.get(CompanyState, str(key))
        return default if row is None else row.value

    def set_state(self, key: StateKey, value: Any) -> None:
        row = self.db.get(CompanyState, str(key))
        if row is None:
            self.db.add(CompanyState(key=str(key), value=value, updated_by=self.agent))
        else:
            row.value = value
            row.updated_by = self.agent
        self.db.flush()

    def check(self, kind: OutboundKind, content: str = "", **meta: Any):
        from app.agents.guardrails import check_outbound

        return check_outbound(self, kind, content, **meta)


class Agent:
    name: ClassVar[AgentName]
    every_minutes: ClassVar[int | None] = None
    handles: ClassVar[tuple[JobType, ...]] = ()

    def run(self, ctx: AgentContext, job: Job | None = None) -> None:
        raise NotImplementedError
