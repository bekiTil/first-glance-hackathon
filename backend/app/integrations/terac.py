"""Terac: real people answer our questions (required by the hackathon). Owner: Yared.

  request_quote(task, count) -> {"request_id", "cpi_usd", "eta"}
  launch(request_id)         -> study id
  get_submissions(study_id)  -> list[dict]   one answer per person

Terac's MCP tools (terac_request_feasibility, terac_launch_draft_opportunity,
terac_get_submissions) need a browser login. If Terac has no server API key, run the
Research agent from Claude Code with the Terac MCP and write results into the `studies`
table instead. Launch studies for the General Population (fastest).
Install: claude mcp add --transport http terac https://terac.com/api/mcp
"""

from app.config import settings


def request_quote(task: str, count: int) -> dict:
    if settings.mock_terac:
        return {"request_id": "mock-req-1", "cpi_usd": 1.5, "eta": "30m"}
    raise NotImplementedError("TODO(Yared): Terac API, or run Study via Claude Code MCP")


def launch(request_id: str) -> str:
    if settings.mock_terac:
        return "mock-study-1"
    raise NotImplementedError("TODO(Yared)")


def get_submissions(study_id: str) -> list[dict]:
    if settings.mock_terac:
        # Deal-preference answers: which of 3 listings each person picked and why.
        return [
            {"picked": "B", "why": "Lower level is worth $15 more"},
            {"picked": "B", "why": "Friday is easier"},
            {"picked": "A", "why": "Cheapest"},
        ]
    raise NotImplementedError("TODO(Yared)")
