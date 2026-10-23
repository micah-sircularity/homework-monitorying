"""Reconstruct a conversation result and aggregate each agent run's usage once."""

import json
import re
from datetime import datetime
from typing import Any

from pydantic import TypeAdapter
from pydantic_ai import AgentRunResult
from pydantic_ai.messages import (
    ModelMessagesTypeAdapter,
    ModelRequest,
    ModelResponse,
    SystemPromptPart,
    TextPart,
    ThinkingPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)


def fetch_trace(client: Any, trace_id: str, *, min_timestamp: datetime) -> list[dict]:
    """Download completed spans for one trace using an authenticated query client."""
    if not re.fullmatch(r"[0-9a-f]{32}", trace_id):
        raise ValueError("trace_id must be 32 lowercase hexadecimal characters")
    data = client.query_json_rows(
        sql=(
            "SELECT span_id, parent_span_id, span_name, start_timestamp, attributes "
            f"FROM records WHERE trace_id = '{trace_id}' AND kind = 'span' "
            "ORDER BY start_timestamp LIMIT 10000"
        ),
        min_timestamp=min_timestamp,
    )
    rows = data["rows"]
    if len(rows) >= 10000:
        raise ValueError("Trace hit the download limit; refusing a partial replay")
    return rows


def _decode(value: Any) -> Any:
    return json.loads(value) if isinstance(value, str) else value


def _messages(value: Any) -> list:
    messages = _decode(value)
    if not messages:
        raise ValueError("Agent span has no recorded conversation messages")
    if "kind" in messages[0]:
        return ModelMessagesTypeAdapter.validate_python(messages)
    converted = []
    for message in messages:
        role = message["role"]
        parts = []
        for part in message["parts"]:
            kind = part["type"]
            if kind == "text":
                cls = TextPart if role == "assistant" else SystemPromptPart if role == "system" else UserPromptPart
                parts.append(cls(part["content"]))
            elif kind == "thinking":
                parts.append(ThinkingPart(part["content"]))
            elif kind == "tool_call":
                parts.append(ToolCallPart(part["name"], part["arguments"], tool_call_id=part["id"]))
            elif kind == "tool_call_response":
                parts.append(ToolReturnPart(part["name"], part["result"], tool_call_id=part["id"]))
            else:
                raise ValueError(f"Unsupported recorded message part: {kind}")
        converted.append(ModelResponse(parts=parts) if role == "assistant" else ModelRequest(parts=parts))
    return converted


def replay_trace(rows: list[dict]) -> AgentRunResult[str]:
    """Combine all old/current agent spans; retain the latest full message history.

    Nested model spans already contribute to agent totals and must not be added
    again. This helper supports the text/tool message formats used by this quiz.
    """
    runs = []
    seen = set()
    for row in sorted(rows, key=lambda r: r["start_timestamp"]):
        name = row["span_name"]
        if name != "agent run" and not name.startswith("invoke_agent "):
            continue
        if row["span_id"] not in seen:
            seen.add(row["span_id"])
            runs.append(_decode(row["attributes"]))
    if not runs:
        raise ValueError("No agent run or invoke_agent spans found")

    def count(attributes: dict, *keys: str) -> int:
        for key in keys:
            if key in attributes:
                return int(attributes[key])
        return 0

    usage = {
        "input_tokens": sum(count(a, "gen_ai.aggregated_usage.input_tokens", "gen_ai.usage.input_tokens") for a in runs),
        "output_tokens": sum(count(a, "gen_ai.aggregated_usage.output_tokens", "gen_ai.usage.output_tokens") for a in runs),
        "cache_read_tokens": sum(count(a, "gen_ai.aggregated_usage.cache_read.input_tokens", "gen_ai.usage.cache_read.input_tokens", "gen_ai.aggregated_usage.details.cache_read_tokens", "gen_ai.usage.details.cache_read_tokens") for a in runs),
        "requests": sum(row["span_name"].startswith("chat ") for row in rows),
    }
    latest = runs[-1]
    return TypeAdapter(AgentRunResult[str]).validate_python({
        "output": latest["final_result"],
        "messages": _messages(latest["pydantic_ai.all_messages"]),
        "new_message_index": 0,
        "usage": usage,
        "metadata": {"replayed_agent_runs": len(runs), "source": "logfire"},
    })
