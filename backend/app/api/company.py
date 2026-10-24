"""Public Company Log + stats (the judges' proof that agents run the company). Owner: Bereket.

TODO(Bereket):
- GET /log: newest DecisionLog rows (limit, optional agent filter) as DecisionOut. Remove private
  keys (email, phone, to) from `data`: this page is public.
- GET /stats: stats.compute_stats(db).
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import todo
from app.db import get_db
from app.enums import AgentName
from app.schemas import DecisionOut, Stats

router = APIRouter(prefix="/api/company", tags=["company"])


@router.get("/log", response_model=list[DecisionOut])
def company_log(
    limit: int = Query(100, le=500), agent: AgentName | None = None, db: Session = Depends(get_db)
) -> list[DecisionOut]:
    raise todo("Bereket", "company log")


@router.get("/stats", response_model=Stats)
def stats(db: Session = Depends(get_db)) -> Stats:
    raise todo("Bereket", "company stats")
