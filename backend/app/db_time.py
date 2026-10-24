import secrets
from datetime import UTC, datetime


def utcnow() -> datetime:
    """Naive UTC. Every datetime in this codebase is naive UTC (SQLite and Postgres agree)."""
    return datetime.now(UTC).replace(tzinfo=None)


def new_public_id() -> str:
    return secrets.token_hex(12)
