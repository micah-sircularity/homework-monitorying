"""Download the grouped trivia session, replay it, and report approximate cost."""

import argparse
import json
from datetime import datetime
from pathlib import Path

from logfire.query_client import LogfireQueryClient
from pydantic import TypeAdapter
from pydantic_ai import AgentRunResult

from helpers.costs import calculate_cost
from trace_replay import fetch_trace, replay_trace

SESSION_TRACE_ID = "01a169edd60318b8442822db1883aea3"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace-id", default=SESSION_TRACE_ID)
    parser.add_argument("--since", default="2026-10-23T18:02:30+00:00")
    args = parser.parse_args()
    credentials = json.loads(Path(".logfire/read_token.json").read_text())
    if credentials["organization"] != "micah-sircularity" or credentials["project_name"] != "demo-test":
        raise ValueError("Expected credentials for micah-sircularity/demo-test")
    with LogfireQueryClient(read_token=credentials["token"], base_url=credentials["base_url"]) as client:
        rows = fetch_trace(client, args.trace_id, min_timestamp=datetime.fromisoformat(args.since))
    result = replay_trace(rows)
    destination = Path(".logfire/replayed_session.json")
    destination.write_bytes(TypeAdapter(AgentRunResult[str]).dump_json(result, indent=2))
    usage = result.usage
    print(json.dumps({
        "trace_id": args.trace_id,
        "agent_runs": result.metadata["replayed_agent_runs"],
        "model_requests": usage.requests,
        "input_tokens": usage.input_tokens,
        "cached_input_tokens": usage.cache_read_tokens,
        "uncached_input_tokens": usage.input_tokens - usage.cache_read_tokens,
        "output_tokens": usage.output_tokens,
        "glm_cost_usd": calculate_cost("glm-5p3-flash", usage.input_tokens, usage.output_tokens, usage.cache_read_tokens),
        "gpt_4o_mini_comparison_usd": calculate_cost("gpt-4o-mini", usage.input_tokens, usage.output_tokens),
        "replayed_result": str(destination),
    }, indent=2))


if __name__ == "__main__":
    main()
