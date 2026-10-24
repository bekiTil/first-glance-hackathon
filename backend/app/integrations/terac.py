"""Terac: real people answer our questions (required by the hackathon). Owner: Yared.

REST API (beta): https://terac.com/api/external/v2, header "Authorization: Bearer <TERAC_API_KEY>".
Key: Terac dashboard -> organization settings -> API keys. Spec: https://terac.com/docs/developers

How a FirstGlance test works: Terac recruits people and sends them to OUR page (task_url =
{PUBLIC_WEB_URL}/t/<test id>), where they see one version for 5 seconds and answer; answers land in
our test_answers table. One Terac opportunity per test.
Audience = Terac's base audience (US adults, any language) = the "General Population" the organizers
asked for. Completion is self-reported, so no callback is needed.

  create_study(title, description, task_url, participants, minutes) -> {"id", "cost_per_participant", "total_cost", "affordable"}
  launch(opportunity_id) -> status string
"""

import httpx

from app.config import settings

BASE_URL = "https://terac.com/api/external/v2"
PROJECT_NAME = "FirstGlance tests"
SCREENER = {
    "key": "uses_websites",
    "text": "Do you sign up for or buy things from websites or apps at least once a month?",
    "pick": "one",
    "answers": [{"text": "Yes", "qualify_logic": "must"}, {"text": "No", "qualify_logic": "reject"}],
}


class TeracError(RuntimeError):
    pass


def _client() -> httpx.Client:
    # creating a draft prices the whole brief server-side, which can take well over 30 s
    return httpx.Client(
        base_url=BASE_URL,
        headers={"Authorization": f"Bearer {settings.terac_api_key}"},
        timeout=httpx.Timeout(120, connect=15),
    )


def _quote(opportunity: dict) -> dict:
    pricing = opportunity.get("pricing") or {}
    return {
        "id": opportunity["id"],
        "cost_per_participant": (pricing.get("cost_per_participant_cents") or 0) / 100,
        "total_cost": (pricing.get("total_cost_cents") or 0) / 100,
        "affordable": (opportunity.get("funding") or {}).get("affordable"),
    }


def _existing_draft(client: httpx.Client, task_url: str, participants: int) -> dict | None:
    """A retry after a timeout must not pile up drafts: reuse the draft that points at this test page."""
    try:
        drafts = _unwrap(client.get("/opportunities", params={"status": "draft"}))
    except (TeracError, httpx.HTTPError):
        return None
    for summary in drafts if isinstance(drafts, list) else []:
        try:  # the list view leaves tasks empty, so read each draft
            opp = _unwrap(client.get(f"/opportunities/{summary['id']}"))
        except (TeracError, httpx.HTTPError, KeyError):
            continue
        same_page = any((t or {}).get("task_url") == task_url for t in opp.get("tasks") or [])
        if same_page and opp.get("num_participants") == participants:  # a different size = a different price
            return opp
    return None


def _unwrap(response: httpx.Response):
    if response.status_code >= 400:
        raise TeracError(
            f"Terac {response.request.method} {response.request.url.path} -> "
            f"{response.status_code}: {response.text[:500]}"
        )
    body = response.json()
    return body.get("data", body) if isinstance(body, dict) else body


def _project_id(client: httpx.Client) -> str:
    projects = _unwrap(client.get("/projects"))
    for project in projects if isinstance(projects, list) else []:
        if project.get("name") == PROJECT_NAME:
            return project["id"]
    return _unwrap(client.post("/projects", json={"name": PROJECT_NAME}))["id"]


def create_study(title: str, description: str, task_url: str, participants: int, minutes: int) -> dict:
    """Create a DRAFT opportunity (nothing charged yet). Returns its id and price."""
    if settings.mock_terac:
        return {
            "id": "mock-opp-1",
            "cost_per_participant": 1.5,
            "total_cost": 1.5 * participants,
            "affordable": True,
        }
    with _client() as client:
        existing = _existing_draft(client, task_url, participants)
        if existing:
            return _quote(existing)
        opportunity = _unwrap(
            client.post(
                "/opportunities",
                json={
                    "title": title,
                    "description": description,
                    "project_id": _project_id(client),
                    "num_participants": participants,
                    "business_type": "b2c",
                    "unrestricted_audience": True,  # US adults 18+: the general population
                    "customer_screening_review": "auto_invite",
                    "screening_questions": [SCREENER],
                    "tasks": [
                        {
                            "sequence": 1,
                            "task_type": "interview",
                            "review_type": "self_report",
                            "task_url": task_url,
                            "title": "Look at a website for 5 seconds",
                            "description": "Open the link, look at a website for 5 seconds, answer 2 quick questions, press Submit, then mark this task done.",
                            "duration_minutes": minutes,
                        }
                    ],
                },
            )
        )
    return _quote(opportunity)


def launch(opportunity_id: str) -> str:
    """Charges the Terac balance (event credits) and starts recruiting."""
    if settings.mock_terac:
        return "active"
    with _client() as client:
        response = client.post(
            f"/opportunities/{opportunity_id}/launch", json={}
        )  # Terac needs a JSON content-type
        if response.status_code == 409:  # not a draft any more: an earlier launch already went through
            current = _unwrap(client.get(f"/opportunities/{opportunity_id}"))
            if current.get("status") not in ("draft", None):
                return current["status"]
        return _unwrap(response)["status"]
