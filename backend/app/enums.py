"""SHARED contract: every status/type string used in the DB and the API.

Owner: Bereket. Do not add or rename values without telling the team. The frontend
gets these through the generated OpenAPI types.
"""

from enum import StrEnum


class TestStatus(StrEnum):
    draft = "draft"  # page read + rewrite made, customer hasn't paid
    awaiting_payment = "awaiting_payment"  # sent to Whop checkout
    paid = "paid"  # Finance recorded the payment; Tester will launch the Terac study
    testing = "testing"  # real people are looking at it right now
    delivered = "delivered"  # results graded + report emailed
    refunded = "refunded"  # our rewrite didn't win -> money back
    failed = "failed"  # something broke; Finance refunds


class TestKind(StrEnum):
    customer = "customer"  # a paying customer's page
    self = "self"  # our own landing page (Research agent dogfooding = the Terac before/after)


class Arm(StrEnum):
    original = "original"
    rewrite = "rewrite"


class Winner(StrEnum):
    original = "original"
    rewrite = "rewrite"
    tie = "tie"


class JobType(StrEnum):
    payment_received = "payment_received"  # Whop webhook -> Finance
    run_test = "run_test"  # payload {"test_id": public_id} -> Tester
    support_message = "support_message"  # contact form -> Support
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
    tester = "tester"
    finance = "finance"
    compliance = "compliance"
    research = "research"


class PaymentStatus(StrEnum):
    succeeded = "succeeded"
    refunded = "refunded"


class OutboundKind(StrEnum):
    """Everything an agent sends into the world goes through guardrails.check_outbound()."""

    email = "email"
    sms = "sms"
    post = "post"
    ad = "ad"
    price_change = "price_change"
    refund = "refund"


class StateKey(StrEnum):
    """Keys in the company_state table (the CEO writes most; everyone reads)."""

    price_usd = "price_usd"
    priorities = "priorities"
    target_audiences = "target_audiences"
    landing_copy = "landing_copy"  # Research agent: the winning copy of OUR landing page
    ad_spend_today = "ad_spend_today"
    kill_switch = "kill_switch"
