"""The `agents` service: runs every agent on its schedule and processes queued jobs.
Owner: Bereket.

  uv run python -m app.worker          run forever (what Railway runs)
  uv run python -m app.worker --once   run every agent once + drain jobs, then exit (dev/testing)
"""

import argparse
import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy import select

from app.agents import ALL_AGENTS
from app.agents.base import Agent, AgentContext
from app.db import init_db, session_scope
from app.db_time import utcnow
from app.enums import JobStatus, JobType
from app.models import DecisionLog, Job

log = logging.getLogger("worker")


def run_agent(agent: Agent, job_id: int | None = None) -> None:
    """Run one agent in its own transaction. A crash is logged, never kills the worker."""
    try:
        with session_scope() as db:
            job = db.get(Job, job_id) if job_id else None
            agent.run(AgentContext(db=db, agent=agent.name), job)
    except NotImplementedError as e:
        # Unfinished agents stay quiet (no Company Log noise); jobs for them are marked failed.
        log.info("agent %s not implemented yet: %s", agent.name, e)
        raise
    except Exception as e:
        log.exception("agent %s failed", agent.name)
        with session_scope() as db:
            db.add(
                DecisionLog(
                    agent=agent.name, action="error", reason=f"{type(e).__name__}: {e}"[:1000], data={}
                )
            )
        raise


def process_jobs(limit: int = 25) -> int:
    with session_scope() as db:
        jobs = db.scalars(
            select(Job)
            .where(Job.status == JobStatus.pending, Job.run_after <= utcnow())
            .order_by(Job.id)
            .limit(limit)
        ).all()
        for job in jobs:
            job.status = JobStatus.running
            job.attempts += 1
        claimed = [(j.id, j.type, j.payload) for j in jobs]

    for job_id, job_type, payload in claimed:
        agents = _agents_for(job_type, payload)
        status, error = JobStatus.done, None
        for agent in agents:
            try:
                run_agent(agent, job_id)
            except Exception as e:
                status, error = JobStatus.failed, f"{agent.name}: {e}"
        with session_scope() as db:
            job = db.get(Job, job_id)
            job.status = status if agents else JobStatus.failed
            job.last_error = error if agents else f"no agent handles {job_type}"
    return len(claimed)


def _agents_for(job_type: str, payload: dict) -> list[Agent]:
    if job_type == JobType.run_agent:
        return [a for a in ALL_AGENTS if a.name == payload.get("agent")]
    return [a for a in ALL_AGENTS if job_type in a.handles]


def run_once() -> None:
    """Every scheduled agent once, then drain the job queue."""
    process_jobs()
    for agent in ALL_AGENTS:
        if agent.every_minutes:
            try:
                run_agent(agent)
            except Exception:
                pass
    process_jobs()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    init_db()
    if args.once:
        run_once()
        return

    scheduler = BlockingScheduler(timezone="UTC")
    for agent in ALL_AGENTS:
        if agent.every_minutes:
            scheduler.add_job(
                _safe,
                "interval",
                minutes=agent.every_minutes,
                args=[agent],
                next_run_time=utcnow(),
                id=str(agent.name),
                max_instances=1,
                coalesce=True,
            )
    scheduler.add_job(process_jobs, "interval", seconds=5, id="jobs", max_instances=1, coalesce=True)
    log.info("agents service started: %s", [str(a.name) for a in ALL_AGENTS])
    scheduler.start()


def _safe(agent: Agent) -> None:
    try:
        run_agent(agent)
    except Exception:
        pass  # already logged to decision_log


if __name__ == "__main__":
    main()
