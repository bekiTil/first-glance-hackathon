"""Claude wrapper used by every agent (shared). Owner: Bereket.

Three helpers:
  ask_text(system, prompt, mock=...)                         -> str
  ask_json(system, prompt, schema, mock=...)                 -> dict  (structured output, schema-guaranteed)
  run_tools(system, prompt, tools, handlers, mock=...)       -> str   (agent loop over your own tools)

Pass `mock=` with what the call should return when MOCK_LLM=true, so the flow runs offline.
Model defaults to claude-opus-5-5 (CLAUDE_MODEL in .env). Refusal fallbacks are enabled:
if a request is declined, the API retries it on a suitable fallback model automatically.
"""

import json
import logging
from collections.abc import Callable
from typing import Any

import anthropic

from app.config import settings

log = logging.getLogger(__name__)

_FALLBACK_BETA = "server-side-fallback-2026-07-01"
_client: anthropic.Anthropic | None = None


class LLMError(RuntimeError):
    pass


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        # .env is read by pydantic-settings, not exported, so pass the key; None -> SDK's own lookup
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key or None)
    return _client


def _create(**kwargs: Any):
    try:
        response = _get_client().beta.messages.create(
            model=settings.claude_model,
            max_tokens=16000,
            betas=[_FALLBACK_BETA],
            fallbacks="default",
            **kwargs,
        )
    except anthropic.RateLimitError as e:
        raise LLMError(f"rate limited: {e.message}") from e
    except anthropic.APIStatusError as e:
        raise LLMError(f"API error {e.status_code}: {e.message}") from e
    except anthropic.APIConnectionError as e:
        raise LLMError("could not reach the Claude API") from e
    if response.stop_reason == "refusal":
        raise LLMError("request was declined")
    return response


def _text(response) -> str:
    return "".join(b.text for b in response.content if b.type == "text")


def ask_text(system: str, prompt: str, *, mock: str, effort: str | None = None) -> str:
    if settings.mock_llm:
        return mock
    response = _create(
        system=system,
        messages=[{"role": "user", "content": prompt}],
        output_config={"effort": effort or settings.claude_effort},
    )
    return _text(response)


def ask_json(system: str, prompt: str, schema: dict, *, mock: dict, effort: str | None = None) -> dict:
    """`schema` is a JSON Schema object. Every object in it needs "additionalProperties": false
    and a full "required" list; use {"anyOf": [{"type": "string"}, {"type": "null"}]} for optional."""
    if settings.mock_llm:
        return mock
    response = _create(
        system=system,
        messages=[{"role": "user", "content": prompt}],
        output_config={
            "effort": effort or settings.claude_effort,
            "format": {"type": "json_schema", "schema": schema},
        },
    )
    return json.loads(_text(response))


def run_tools(
    system: str,
    prompt: str,
    tools: list[dict],
    handlers: dict[str, Callable[[dict], Any]],
    *,
    mock: str,
    effort: str | None = None,
    max_turns: int = 10,
) -> str:
    """Manual agent loop. `tools` are Claude tool definitions (set "strict": True);
    `handlers[name](input_dict)` runs the tool and returns anything JSON-serializable.
    Raise inside a handler to send an error result back to Claude."""
    if settings.mock_llm:
        return mock
    messages: list[dict] = [{"role": "user", "content": prompt}]
    for _ in range(max_turns):
        response = _create(
            system=system,
            messages=messages,
            tools=tools,
            output_config={"effort": effort or settings.claude_effort},
        )
        if response.stop_reason != "tool_use":
            return _text(response)
        messages.append({"role": "assistant", "content": response.content})
        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            try:
                output = handlers[block.name](block.input)
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(output, default=str),
                    }
                )
            except Exception as e:  # report the failure to Claude instead of crashing the agent
                log.warning("tool %s failed: %s", block.name, e)
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": f"Error: {e}",
                        "is_error": True,
                    }
                )
        messages.append({"role": "user", "content": results})
    raise LLMError(f"agent loop did not finish in {max_turns} turns")
