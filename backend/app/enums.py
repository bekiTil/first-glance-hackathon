"""SHARED contract: every status/type string used in the DB and the API.

Owner: Bereket. Do not add or rename values without telling the team. The frontend
gets these through the generated OpenAPI types.
"""

from enum import StrEnum


class WatchStatus(StrEnum):
    draft = "draft"  # checklist built, customer hasn't confirmed
    awaiting_payment = "awaiting_payment"  # sent to Whop checkout
    active = "active"  # paid, watcher is checking every 15 min
    purchased = "purchased"  # customer said they bought
    expired = "expired"  # events passed, at least one match was delivered
    refunded = "refunded"  # events passed with no match -> refunded
    cancelled = "cancelled"


class AlertStatus(StrEnum):
    sent = "sent"
    clicked = "clicked"
    bought = "bought"
    rejected = "rejected"  # "not what I wanted"
    failed = "failed"  # could not deliver


class ReplyAction(StrEnum):
    bought = "bought"  # SMS reply "1"
    keep = "keep"  # SMS reply "2"
    reject = "reject"  # SMS reply "3"


class RejectReason(StrEnum):
    price_higher = "price_higher"
    sold_out = "sold_out"
    wrong_criteria = "wrong_criteria"
    other = "other"


class JobType(StrEnum):
    payment_received = "payment_received"  # Whop webhook -> Finance
    sms_received = "sms_received"  # Twilio inbound -> Support
    email_reply = "email_reply"  # email button click -> Support
    run_agent = "run_agent"  # payload {"agent": AgentName} -> that agent


class JobStatus(StrEnum):
    pending = "pending"
    running = "running"
    done = "done"
    failed = "failed"


class AgentName(StrEnum):
    ceo = "ceo"
    growth = "growth"
    support = "support"
    watcher = "watcher"
    finance = "finance"
    compliance = "compliance"
    research = "research"


class Channel(StrEnum):
    email = "email"
    sms = "sms"


class TicketSource(StrEnum):
    seatgeek = "seatgeek"
    ticketmaster = "ticketmaster"
    mock = "mock"


class PaymentStatus(StrEnum):
    succeeded = "succeeded"
    refunded = "refunded"


class StudyKind(StrEnum):
    deal_preferences = "deal_preferences"  # "which ticket would you buy?"
    landing_page = "landing_page"  # "would you pay $3? what's unclear?"


class StudyStatus(StrEnum):
    quoted = "quoted"
    running = "running"
    completed = "completed"


class OutboundKind(StrEnum):
    """Everything an agent sends into the world goes through guardrails.check_outbound()."""

    email = "email"
    sms = "sms"
    post = "post"
    ad = "ad"
    price_change = "price_change"
    refund = "refund"


class StateKey(StrEnum):
    """Keys in the company_state table (the CEO writes, everyone reads)."""

    price_usd = "price_usd"
    priorities = "priorities"
    target_events = "target_events"
    deal_weights = "deal_weights"
    ad_spend_today = "ad_spend_today"
    kill_switch = "kill_switch"
