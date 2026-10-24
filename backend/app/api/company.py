"""Public Company Log + stats (the judges' proof that agents run the company). Owner: Bereket.

- GET /log: newest DecisionLog rows (limit, optional agent filter) as DecisionOut. Private keys
  (email, phone, to, ...) are removed from `data` at any depth: this page is public.
- GET /stats: stats.compute_stats(db).
"""

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import stats as company_stats
from app.db import get_db
from app.enums import AgentName
from app.models import DecisionLog
from app.schemas import DecisionOut, Stats

router = APIRouter(prefix="/api/company", tags=["company"])

PRIVATE_KEYS = {"email", "phone", "to", "customer_email", "customer_phone", "address", "whop_user_id"}


def scrub(value: Any) -> Any:
    """Drop private keys from nested dicts/lists."""
    if isinstance(value, dict):
        return {k: scrub(v) for k, v in value.items() if str(k).lower() not in PRIVATE_KEYS}
    if isinstance(value, list):
        return [scrub(v) for v in value]
    return value


@router.get("/log", response_model=list[DecisionOut])
def company_log(
    limit: int = Query(100, le=500), agent: AgentName | None = None, db: Session = Depends(get_db)
) -> list[DecisionOut]:
    stmt = select(DecisionLog).order_by(DecisionLog.created_at.desc(), DecisionLog.id.desc()).limit(limit)
    if agent:
        stmt = stmt.where(DecisionLog.agent == agent)
    return [
        DecisionOut(
            id=row.id,
            agent=row.agent,
            action=row.action,
            reason=row.reason,
            data=scrub(row.data or {}),
            created_at=row.created_at,
        )
        for row in db.scalars(stmt)
    ]


@router.get("/stats", response_model=Stats)
def stats(db: Session = Depends(get_db)) -> Stats:
    return company_stats.compute_stats(db)
