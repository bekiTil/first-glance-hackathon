"""Terac: real people answer our questions (required by the hackathon). Owner: Yared.

REST API (beta): https://terac.com/api/external/v2, header "Authorization: Bearer <TERAC_API_KEY>".
Key: Terac dashboard -> organization settings -> API keys. Spec: https://terac.com/docs/developers

How a study works here: Terac recruits people and sends them to OUR page (task_url =
{PUBLIC_WEB_URL}/study/<id>), where they answer; answers land in our study_answers table.
Audience = Terac's base audience (US adults, any language) = the "General Population" the organizers
asked for. Completion is self-reported, so no callback is needed.

  create_study(title, description, task_url, participants, minutes) -> {"id", "cost_per_participant", "total_cost", "affordable"}
  launch(opportunity_id) -> status string
"""

import httpx

from app.config import settings

BASE_URL = "https://terac.com/api/external/v2"
PROJECT_NAME = "Ticket Watch research"
SCREENER = {
    "key": "bought_tickets",
    "text": "Have you bought tickets to a live sports game, concert, or show in the past 2 years?",
    "pick": "one",
    "answers": [{"text": "Yes", "qualify_logic": "must"}, {"text": "No", "qualify_logic": "reject"}],
}


class TeracError(RuntimeError):
    pass


def _client() -> httpx.Client:
    return httpx.Client(
        base_url=BASE_URL, headers={"Authorization": f"Bearer {settings.terac_api_key}"}, timeout=30
    )


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
                            "title": "Pick the tickets you'd buy",
                            "description": "Open the link, answer 6 quick questions, press Submit, then mark this task done.",
                            "duration_minutes": minutes,
                        }
                    ],
                },
            )
        )
    pricing = opportunity.get("pricing") or {}
    return {
        "id": opportunity["id"],
        "cost_per_participant": (pricing.get("cost_per_participant_cents") or 0) / 100,
        "total_cost": (pricing.get("total_cost_cents") or 0) / 100,
        "affordable": (opportunity.get("funding") or {}).get("affordable"),
    }


def launch(opportunity_id: str) -> str:
    """Charges the Terac balance (event credits) and starts recruiting."""
    if settings.mock_terac:
        return "active"
    with _client() as client:
        return _unwrap(client.post(f"/opportunities/{opportunity_id}/launch"))["status"]
