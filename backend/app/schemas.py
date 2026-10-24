"""SHARED contract: Pydantic shapes passed between modules and returned by the API.

Owner: Bereket. These generate openapi.json -> frontend/src/api/types.ts
(run `uv run python scripts/export_openapi.py` then `npm run gen:api`).
All datetimes are naive UTC.
"""

from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field

from app.enums import (
    AgentName,
    AlertStatus,
    Channel,
    PaymentStatus,
    ReplyAction,
    TicketSource,
    WatchStatus,
)

# ---------- domain ----------


class Checklist(BaseModel):
    """What the customer confirms before paying. A match = every field below is satisfied."""

    query: str = Field(description="The customer's original sentence")
    performer: str = Field(description='Team/artist/show, e.g. "New York Knicks"')
    venue: str | None = None
    date_from: date
    date_to: date
    weekdays: list[int] = Field(default_factory=list, description="0=Mon..6=Sun; empty = any day")
    max_price_per_ticket: float = Field(description="USD per ticket, all-in including fees")
    quantity: int = 1
    exclude_sections: list[str] = Field(default_factory=list, description='e.g. ["upper level"]')
    preferences: list[str] = Field(default_factory=list, description="Soft wishes; ranked, never guaranteed")


class EventInfo(BaseModel):
    source: TicketSource
    external_id: str
    name: str
    starts_at: datetime
    venue: str
    url: str


class Listing(BaseModel):
    """The best current offer for one event, as returned by integrations.tickets."""

    source: TicketSource
    external_event_id: str
    event_name: str
    starts_at: datetime
    venue: str
    price_per_ticket: float
    includes_fees: bool = False
    quantity_available: int | None = None
    section: str | None = None
    url: str

    @property
    def key(self) -> str:
        """Same listing at the same price = same key (used to avoid duplicate alerts)."""
        return f"{self.source}:{self.external_event_id}:{self.section or '-'}:{self.price_per_ticket:.2f}"


class Verification(BaseModel):
    """Result of integrations.solari.verify_listing()."""

    ok: bool
    price_seen: float | None = None
    screenshot_path: str | None = None
    note: str = ""


class PaymentEvent(BaseModel):
    """Normalized Whop payment webhook (integrations.whop.parse_webhook)."""

    whop_payment_id: str
    whop_user_id: str | None = None
    email: str | None = None
    watch_public_id: str
    amount: float
    currency: str = "usd"
    status: PaymentStatus = PaymentStatus.succeeded


class FreeEvent(BaseModel):
    title: str
    url: str
    when: str | None = None
    where: str | None = None
    summary: str | None = None


# ---------- API requests ----------


class CreateWatchRequest(BaseModel):
    query: str = Field(min_length=3, examples=["Knicks under $80, any Friday in November, 2 seats"])
    email: EmailStr
    phone: str | None = Field(default=None, description="E.164, e.g. +12125551234")
    sms_consent: bool = False


class UpdateChecklistRequest(BaseModel):
    checklist: Checklist


class SendCodeRequest(BaseModel):
    watch_id: str
    phone: str


class VerifyCodeRequest(BaseModel):
    phone: str
    code: str


class LoginRequest(BaseModel):
    email: EmailStr


# ---------- API responses ----------


class WatchOut(BaseModel):
    id: str = Field(description="public id (never the DB integer)")
    status: WatchStatus
    checklist: Checklist
    questions: list[str] = Field(
        default_factory=list, description="Follow-ups if the request was missing info"
    )
    events: list[EventInfo] = Field(default_factory=list)
    price_usd: float
    phone_verified: bool = False
    created_at: datetime


class CheckoutOut(BaseModel):
    checkout_url: str


class VerifyOut(BaseModel):
    verified: bool


class OkOut(BaseModel):
    ok: bool = True
    message: str = ""


class AlertOut(BaseModel):
    id: int
    status: AlertStatus
    listing: Listing
    deal_score: float
    channels: list[Channel]
    sent_at: datetime


class DecisionOut(BaseModel):
    id: int
    agent: AgentName
    action: str
    reason: str
    data: dict
    created_at: datetime


class Stats(BaseModel):
    revenue_usd: float
    payments: int
    refunds: int
    watches_created: int
    watches_active: int
    alerts_sent: int
    clicks: int
    purchases: int
    conversion_rate: float = Field(description="paid watches / created watches")
    price_usd: float


class ReplyIn(BaseModel):
    """Payload of email_reply / sms_received jobs, consumed by the Support agent."""

    alert_id: int | None = None
    phone: str | None = None
    action: ReplyAction | None = None
    text: str = ""


# ---------- Research / Terac studies (owner: Yared) ----------


class StudyOption(BaseModel):
    label: str = Field(description='"A" | "B" | "C"')
    price: float
    section: str
    lower_level: bool
    day: str = Field(description='e.g. "Fri Nov 13"')
    weekend: bool


class StudySet(BaseModel):
    event: str
    options: list[StudyOption]


class LandingCopy(BaseModel):
    headline: str
    subhead: str
    bullets: list[str] = Field(default_factory=list)
    version: int = 1


class StudyOut(BaseModel):
    """What the /study/:id page shows a Terac participant."""

    id: str
    round: int
    sets: list[StudySet]
    landing: LandingCopy
    price_usd: float


class StudyPick(BaseModel):
    set: int
    option: str
    why: str = ""


class StudyAnswerIn(BaseModel):
    participant_ref: str | None = Field(default=None, description="teracSubmissionId from the task URL")
    picks: list[StudyPick]
    willingness: int = Field(ge=1, le=5, description="How likely to pay $3 for this (1-5)")
    unclear: str = ""
