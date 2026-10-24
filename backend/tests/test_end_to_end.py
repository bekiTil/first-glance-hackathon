"""Team finish line: the whole flow in mock mode.

request -> checklist -> phone code -> pay -> watcher alert by email + text -> reply -> purchased.
Skipped until the owners' parts land. Remove the skip line and make it pass together.
"""

import pytest
from fastapi.testclient import TestClient

from app.integrations import notify, tickets
from app.main import app
from app.worker import process_jobs, run_once

pytestmark = pytest.mark.skip(
    reason="turn on when watches/phone routes, Watcher, Finance, Support, "
    "links and company stats are implemented"
)


def test_full_flow():
    with TestClient(app) as client:
        r = client.post(
            "/api/watches",
            json={
                "query": "Knicks under $80, any Friday, 2 seats",
                "email": "fan@example.com",
                "phone": "+12125550100",
                "sms_consent": True,
            },
        )
        assert r.status_code == 200, r.text
        watch = r.json()
        assert watch["status"] == "draft"
        assert watch["checklist"]["max_price_per_ticket"] == 80
        assert watch["events"], "mock tickets should find Friday events"
        wid = watch["id"]

        # verify phone (mock code)
        assert (
            client.post("/api/phone/send-code", json={"watch_id": wid, "phone": "+12125550100"}).status_code
            == 200
        )
        assert client.post("/api/phone/verify", json={"phone": "+12125550100", "code": "123456"}).json()[
            "verified"
        ]

        # confirm -> fake Whop checkout -> payment job -> Finance activates the watch
        checkout = client.post(f"/api/watches/{wid}/confirm").json()["checkout_url"]
        assert "/api/dev/fake-pay/" in checkout
        assert client.get(f"/api/dev/fake-pay/{wid}", follow_redirects=False).status_code == 302
        process_jobs()
        assert client.get(f"/api/watches/{wid}").json()["status"] == "active"

        # price drops under $80 -> watcher alerts by email + text
        tickets.MOCK_PRICE_OVERRIDE = 60.0
        notify.OUTBOX.clear()
        run_once()
        channels = {m["channel"] for m in notify.OUTBOX if "Ticket Watch code" not in m["body"]}
        assert {"email", "sms"} <= channels, notify.OUTBOX

        # second run at the same price: no duplicate alert
        before = len(notify.OUTBOX)
        run_once()
        assert len([m for m in notify.OUTBOX[before:] if "$60" in m["body"]]) == 0

        # customer taps "I bought it" in the email
        from app.db import session_scope
        from app.models import Alert

        with session_scope() as db:
            token = db.query(Alert).first().token
        assert client.get(f"/go/{token}", follow_redirects=False).status_code == 302
        assert client.get(f"/api/reply/{token}/bought", follow_redirects=False).status_code == 302
        process_jobs()
        assert client.get(f"/api/watches/{wid}").json()["status"] == "purchased"

        stats = client.get("/api/company/stats").json()
        assert stats["revenue_usd"] == 3.0 and stats["purchases"] == 1 and stats["clicks"] == 1
        log = client.get("/api/company/log").json()
        actions = {e["action"] for e in log}
        assert {
            "built_checklist",
            "payment_recorded",
            "sent_alert",
            "marked_purchased",
            "hourly_report",
        } <= actions
        assert all("email" not in e["data"] for e in log)

        tickets.MOCK_PRICE_OVERRIDE = None


def test_guardrails_block_bad_price():
    from app.agents.base import AgentContext
    from app.db import session_scope
    from app.enums import AgentName, OutboundKind

    with session_scope() as db:
        ctx = AgentContext(db=db, agent=AgentName.ceo)
        assert not ctx.check(OutboundKind.price_change, new_price=50)
        assert ctx.check(OutboundKind.price_change, new_price=4)
