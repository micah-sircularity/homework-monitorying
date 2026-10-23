"""A trivia agent with Open Trivia DB tools and Logfire tracing."""

import argparse
import os

import logfire
from pydantic_ai import Agent
from pydantic_ai.capabilities import Caching
from pydantic_ai.models.test import TestModel

from tools import TriviaTools


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("prompt", nargs="?", default="Show me the available trivia categories.")
    parser.add_argument("--smoke", action="store_true", help="Use TestModel without a provider API key.")
    args = parser.parse_args()
    model = os.environ.get("PYDANTIC_AI_MODEL")
    if not args.smoke and not model:
        parser.error("Set PYDANTIC_AI_MODEL=provider:model and its provider API key, or use --smoke.")

    logfire.configure(
        service_name="homework-monitoring",
        service_version="0.1.0",
        environment="development",
    )
    logfire.instrument_pydantic_ai()
    trivia_tools = TriviaTools()
    agent = Agent(
        TestModel(call_tools=[]) if args.smoke else model,
        name="trivia_agent",
        instructions=(
            "Host a trivia game. Use get_categories to look up category IDs and "
            "get_questions to fetch questions for the user's category and difficulty. "
            "Ask one question at a time with shuffled answer choices. Keep correct "
            "answers hidden until the user answers, then give feedback and track their score. "
            "If the API is rate limited, tell the user to wait before trying again."
        ),
        tools=[trivia_tools.get_categories, trivia_tools.get_questions],
        capabilities=[Caching()],
    )
    try:
        result = agent.run_sync(args.prompt)
        print(result.output)
    finally:
        logfire.force_flush()


if __name__ == "__main__":
    main()
