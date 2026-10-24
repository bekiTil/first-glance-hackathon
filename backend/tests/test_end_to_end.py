"""Team finish line: the whole FirstGlance flow in mock mode.

order -> page read + rewrite -> pay -> Terac study launched -> people answer -> graded -> report
-> refund if our rewrite lost. Skipped until the owners' parts land: remove the skip line together.
"""

import pytest
from fastapi.testclient import TestClient

from app.integrations import notify
from app.main import app
from app.worker import process_jobs, run_once

pytestmark = pytest.mark.skip(
    reason="turn on when tests routes, Tester, Finance, test page and stats are built"
)


def test_full_flow():
    with TestClient(app) as client:
        r = client.post(
            "/api/tests",
            json={
                "url": "https://example.com",
                "what_you_do": "Payroll for dentists",
                "email": "founder@example.com",
            },
        )
        assert r.status_code == 200, r.text
        test = r.json()
        assert test["status"] == "draft" and test["original"]["headline"] and test["rewrite"]["headline"]
        tid = test["id"]

        checkout = client.post(f"/api/tests/{tid}/confirm").json()["checkout_url"]
        assert "/api/dev/fake-pay/" in checkout
        client.get(f"/api/dev/fake-pay/{tid}", follow_redirects=False)
        process_jobs()  # Finance records payment + queues run_test; Tester launches the study
        process_jobs()
        assert client.get(f"/api/tests/{tid}").json()["status"] == "testing"

        # a participant opens the test page and answers
        page = client.get(f"/api/t/{tid}?participant=p1").json()
        assert page["arm"] in ("original", "rewrite") and page["hero"]["headline"] and page["seconds"] == 10
        body = {"participant_ref": "p1", "arm": page["arm"], "answer": "payroll for dentists", "signup": 4}
        assert client.post(f"/api/t/{tid}/answers", json=body).status_code == 200
        client.post(f"/api/dev/fake-answers/{tid}?n=10")

        notify.OUTBOX.clear()
        run_once()  # Tester grades + delivers; Finance refunds if the rewrite lost
        report = client.get(f"/api/tests/{tid}").json()
        assert report["status"] in ("delivered", "refunded") and report["results"]["summary"]
        assert any(f"/report/{tid}" in m["body"] for m in notify.OUTBOX)

        stats = client.get("/api/company/stats").json()
        assert stats["payments"] == 1 and stats["tests_delivered"] == 1
        actions = {e["action"] for e in client.get("/api/company/log").json()}
        assert {"read_page", "payment_recorded", "launched_test", "delivered_report"} <= actions
