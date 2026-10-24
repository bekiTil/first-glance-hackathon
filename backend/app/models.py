"""SHARED contract: database tables. Owner: Bereket (payments: Natnael, test_answers: Yared).

Tables are created automatically by db.init_db() (no migrations for the hackathon).
If you need a new column, ask Bereket; deleting backend/dev.db resets your local DB.
All datetimes are naive UTC (use app.db_time.utcnow()).
"""

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.db_time import new_public_id, utcnow


class Base(DeclarativeBase):
    pass


class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(primary_key=True)
    whop_user_id: Mapped[str | None] = mapped_column(String(64), unique=True)
    email: Mapped[str] = mapped_column(String(320), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class PageTest(Base):
    """One FirstGlance test: original hero vs. our rewrite, shown to real people via Terac."""

    __tablename__ = "page_tests"
    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, default=new_public_id)
    kind: Mapped[str] = mapped_column(String(16), default="customer")  # enums.TestKind
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"), index=True)  # None for self
    url: Mapped[str] = mapped_column(Text)
    what_you_do: Mapped[str] = mapped_column(Text)
    original: Mapped[dict | None] = mapped_column(JSON)  # schemas.HeroCopy
    rewrite: Mapped[dict | None] = mapped_column(JSON)  # schemas.HeroCopy
    screenshot_path: Mapped[str | None] = mapped_column(Text)  # Solari screenshot of their page
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)  # enums.TestStatus
    terac_id: Mapped[str | None] = mapped_column(String(128))
    terac_quote: Mapped[dict] = mapped_column(JSON, default=dict)
    results: Mapped[dict | None] = mapped_column(JSON)  # schemas.TestResults
    price_paid: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    launched_at: Mapped[datetime | None] = mapped_column(DateTime)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime)


class TestAnswer(Base):
    """Owner: Yared. One participant's answer, posted from our /t/:id page (the Terac task_url)."""

    __tablename__ = "test_answers"
    __table_args__ = (UniqueConstraint("test_id", "participant_ref"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    test_id: Mapped[int] = mapped_column(ForeignKey("page_tests.id"), index=True)
    participant_ref: Mapped[str] = mapped_column(String(128))
    arm: Mapped[str] = mapped_column(String(16))  # enums.Arm
    answer: Mapped[str] = mapped_column(Text)
    signup: Mapped[int] = mapped_column(Integer)
    understood: Mapped[bool | None] = mapped_column(Boolean)  # graded by the Tester agent
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Payment(Base):
    """Owner: Natnael. Written only by the Finance agent."""

    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    whop_payment_id: Mapped[str] = mapped_column(String(128), unique=True)
    whop_user_id: Mapped[str | None] = mapped_column(String(64))
    test_id: Mapped[int] = mapped_column(ForeignKey("page_tests.id"), index=True)
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8), default="usd")
    status: Mapped[str] = mapped_column(String(32), default="succeeded")  # enums.PaymentStatus
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class CompanyState(Base):
    """Shared brain. Keys: enums.StateKey."""

    __tablename__ = "company_state"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[dict | list | str | float | int | bool | None] = mapped_column(JSON)
    updated_by: Mapped[str] = mapped_column(String(32))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class DecisionLog(Base):
    """Append-only. Every agent action + its reason. Powers the public Company Log page."""

    __tablename__ = "decision_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    agent: Mapped[str] = mapped_column(String(32), index=True)  # enums.AgentName
    action: Mapped[str] = mapped_column(String(100))
    reason: Mapped[str] = mapped_column(Text)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class Job(Base):
    """Work queue. API routes enqueue; the worker runs the matching agent."""

    __tablename__ = "jobs"
    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(32), index=True)  # enums.JobType
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)  # enums.JobStatus
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
    run_after: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
