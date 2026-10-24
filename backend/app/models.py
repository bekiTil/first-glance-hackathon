"""SHARED contract: database tables. Owner: Bereket (payments table: Natnael).

Tables are created automatically by db.init_db() (no migrations for the hackathon).
If you need a new column, ask Bereket; deleting backend/dev.db resets your local DB.
All datetimes are naive UTC (use app.db.utcnow()).
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
    phone: Mapped[str | None] = mapped_column(String(32), index=True)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    sms_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Watch(Base):
    __tablename__ = "watches"
    id: Mapped[int] = mapped_column(primary_key=True)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, default=new_public_id)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    query: Mapped[str] = mapped_column(Text)
    checklist: Mapped[dict] = mapped_column(JSON)  # schemas.Checklist
    questions: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)  # enums.WatchStatus
    price_paid: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class Event(Base):
    """One real-world event; checked once per interval no matter how many watches share it."""

    __tablename__ = "events"
    __table_args__ = (UniqueConstraint("source", "external_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(32))  # enums.TicketSource
    external_id: Mapped[str] = mapped_column(String(128))
    name: Mapped[str] = mapped_column(String(300))
    starts_at: Mapped[datetime] = mapped_column(DateTime)
    venue: Mapped[str] = mapped_column(String(300))
    url: Mapped[str] = mapped_column(Text)
    lowest_price: Mapped[float | None] = mapped_column(Float)
    checked_at: Mapped[datetime | None] = mapped_column(DateTime)


class WatchEvent(Base):
    __tablename__ = "watch_events"
    watch_id: Mapped[int] = mapped_column(ForeignKey("watches.id"), primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), primary_key=True)


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(primary_key=True)
    watch_id: Mapped[int] = mapped_column(ForeignKey("watches.id"), index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    listing: Mapped[dict] = mapped_column(JSON)  # schemas.Listing
    listing_key: Mapped[str] = mapped_column(String(300))
    deal_score: Mapped[float] = mapped_column(Float, default=0.0)
    channels: Mapped[list] = mapped_column(JSON, default=list)  # [enums.Channel]
    delivery_ids: Mapped[dict] = mapped_column(JSON, default=dict)  # proof it was sent
    token: Mapped[str] = mapped_column(String(32), unique=True, default=new_public_id)
    screenshot_path: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="sent")  # enums.AlertStatus
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Click(Base):
    __tablename__ = "clicks"
    id: Mapped[int] = mapped_column(primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id"), index=True)
    clicked_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Outcome(Base):
    __tablename__ = "outcomes"
    id: Mapped[int] = mapped_column(primary_key=True)
    watch_id: Mapped[int] = mapped_column(ForeignKey("watches.id"), index=True)
    alert_id: Mapped[int | None] = mapped_column(ForeignKey("alerts.id"))
    bought: Mapped[bool | None] = mapped_column(Boolean)
    reason: Mapped[str | None] = mapped_column(String(64))  # enums.RejectReason
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Payment(Base):
    """Owner: Natnael. Written only by the Finance agent."""

    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    whop_payment_id: Mapped[str] = mapped_column(String(128), unique=True)
    whop_user_id: Mapped[str | None] = mapped_column(String(64))
    watch_id: Mapped[int] = mapped_column(ForeignKey("watches.id"), index=True)
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(8), default="usd")
    status: Mapped[str] = mapped_column(String(32), default="succeeded")  # enums.PaymentStatus
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class CompanyState(Base):
    """Shared brain. Keys: enums.StateKey. The CEO writes; everyone reads."""

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


class PhoneCode(Base):
    __tablename__ = "phone_codes"
    id: Mapped[int] = mapped_column(primary_key=True)
    phone: Mapped[str] = mapped_column(String(32), index=True)
    code_hash: Mapped[str] = mapped_column(String(128))
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used: Mapped[bool] = mapped_column(Boolean, default=False)


class LoginToken(Base):
    __tablename__ = "login_tokens"
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    token: Mapped[str] = mapped_column(String(32), unique=True, default=new_public_id)
    expires_at: Mapped[datetime] = mapped_column(DateTime)


class Study(Base):
    """Owner: Yared. One Terac study (Study 1 / Study 2)."""

    __tablename__ = "studies"
    id: Mapped[int] = mapped_column(primary_key=True)
    terac_id: Mapped[str | None] = mapped_column(String(128))
    kind: Mapped[str] = mapped_column(String(32))  # enums.StudyKind
    round: Mapped[int] = mapped_column(Integer, default=1)  # 1 = before, 2 = after
    status: Mapped[str] = mapped_column(String(32), default="quoted")  # enums.StudyStatus
    request: Mapped[dict] = mapped_column(JSON, default=dict)
    results: Mapped[dict] = mapped_column(JSON, default=dict)
    launched_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
