"""SHARED contract: Pydantic shapes passed between modules and returned by the API.

Owner: Bereket. These generate openapi.json -> frontend/src/api/types.ts
(run `uv run python scripts/export_openapi.py` then `npm run gen:api`).
All datetimes are naive UTC.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.enums import AgentName, Arm, PaymentStatus, TestStatus, Winner

# ---------- domain ----------


class HeroCopy(BaseModel):
    """The top of a landing page: what a visitor sees in the first 10 seconds."""

    headline: str
    subhead: str = ""
    cta: str = Field(default="", description='Button text, e.g. "Start free trial"')


class ArmResult(BaseModel):
    responses: int
    understood: int = Field(description="Answers Claude graded as matching what the company does")
    understood_rate: float = Field(description="understood / responses, 0..1")
    avg_signup: float = Field(description="Average 'would you sign up?' 1-5")
    sample_answers: list[str] = Field(default_factory=list, description="Up to 5 verbatim answers")


class TestResults(BaseModel):
    original: ArmResult
    rewrite: ArmResult
    winner: Winner
    summary: str = Field(description='One sentence, e.g. "3/5 understood yours, 5/5 understood ours"')


class PaymentEvent(BaseModel):
    """Normalized Whop payment webhook (integrations.whop.parse_webhook)."""

    whop_payment_id: str
    whop_user_id: str | None = None
    email: str | None = None
    test_public_id: str
    amount: float
    currency: str = "usd"
    status: PaymentStatus = PaymentStatus.succeeded


# ---------- API requests ----------


class CreateTestRequest(BaseModel):
    url: str = Field(examples=["https://example.com"])
    what_you_do: str = Field(min_length=5, description="One sentence: what does your company do, for whom?")
    email: EmailStr


class TestAnswerIn(BaseModel):
    participant_ref: str | None = Field(default=None, description="teracSubmissionId from the task URL")
    arm: Arm = Field(description="The arm the test page was given by GET /api/t/{id}")
    answer: str = Field(min_length=1, max_length=1000, description='"What does this company do?"')
    signup: int = Field(ge=1, le=5, description='"How likely are you to sign up?" 1-5')


class SupportRequest(BaseModel):
    email: EmailStr
    message: str = Field(min_length=2, max_length=4000)
    test_id: str | None = None


# ---------- API responses ----------


class TestOut(BaseModel):
    """A customer's test, shown on the order page and the report page."""

    id: str = Field(description="public id (never the DB integer)")
    status: TestStatus
    url: str
    what_you_do: str
    original: HeroCopy | None = None
    rewrite: HeroCopy | None = None
    price_usd: float
    responses_so_far: int = 0
    results: TestResults | None = None
    created_at: datetime


class TestPageOut(BaseModel):
    """What one Terac participant sees on /t/{id}: ONE arm, for `seconds` seconds."""

    id: str
    arm: Arm
    hero: HeroCopy
    seconds: int = 5


class CheckoutOut(BaseModel):
    checkout_url: str


class OkOut(BaseModel):
    ok: bool = True
    message: str = ""


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
    tests_created: int
    tests_paid: int
    tests_delivered: int
    rewrite_win_rate: float = Field(description="delivered customer tests where our rewrite won, 0..1")
    conversion_rate: float = Field(description="paid tests / created tests")
    price_usd: float


class SelfTestOut(BaseModel):
    """Our own landing page's before/after (Research agent), for the Company Log page."""

    status: TestStatus | None = None
    original: HeroCopy | None = None
    rewrite: HeroCopy | None = None
    results: TestResults | None = None
