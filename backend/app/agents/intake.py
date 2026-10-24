"""Request -> checklist (part of the Watcher). Owner: Bereket.

TODO(Bereket): implement build_checklist(). Spec:
- Called synchronously by POST /api/watches (the customer is waiting on the page).
- Use llm.ask_json(system, prompt, schema, mock=...) to turn the sentence into the fields of
  schemas.Checklist (except `query`) plus a list of follow-up `questions` for anything missing
  (price, quantity, what/when). Give the model today's date so dates come back absolute.
- Structured-output schema rules: every object needs "additionalProperties": false and a full
  "required" list; optional values use {"anyOf": [{"type": "string"}, {"type": "null"}]}.
- Requirements only from what the customer said; soft wishes go in `preferences`.
- Pass a realistic `mock=` dict so MOCK_LLM=true still works.
"""

from datetime import date

from app.schemas import Checklist


def build_checklist(query: str, today: date) -> tuple[Checklist, list[str]]:
    """Returns (checklist, follow_up_questions)."""
    raise NotImplementedError("TODO(Bereket): intake")
