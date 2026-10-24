"""Engine + sessions. SQLite locally, Postgres on Railway (same code). Owner: Bereket."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.db_time import new_public_id, utcnow  # noqa: F401  (re-exported for convenience)
from app.models import Base


def _normalize(url: str) -> str:
    # Railway gives postgres:// or postgresql://; SQLAlchemy + psycopg3 wants postgresql+psycopg://
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix) :]
    return url


_url = _normalize(settings.database_url)
engine = create_engine(
    _url,
    connect_args={"check_same_thread": False} if _url.startswith("sqlite") else {},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(engine)
    settings.data_dir.mkdir(parents=True, exist_ok=True)


@contextmanager
def session_scope() -> Iterator[Session]:
    """For the worker and scripts: commits on success, rolls back on error."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db() -> Iterator[Session]:
    """FastAPI dependency."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
