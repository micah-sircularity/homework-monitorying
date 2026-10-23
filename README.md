<img src="assets/icon.svg" width="64" height="64" alt="">

# homework-monitorying

Created in [T3 Code](https://t3.codes).

Python 3.12 environment managed by uv, with Pydantic AI and Logfire.

The trivia agent exposes `get_categories` and `get_questions` from
`tools/trivia_tools.py`. Shared HTTP handling lives in `helpers/trivia_api.py`.
Questions and answers come from [Open Trivia DB](https://opentdb.com/), under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).

Play interactively with Fireworks AI (the key prompt hides your input and does
not save the key to disk):

```bash
uv run python trivia_agent.py --ask-key
```

If `FIREWORKS_API_KEY` is already set, omit `--ask-key`. The default model is
`fireworks:accounts/fireworks/models/glm-5p3-flash`; override it with
`PYDANTIC_AI_MODEL` using another Fireworks model identifier.
Conversation history is kept in memory so the agent can score answers across
turns. Type `quit` to exit. The CLI prints the first tool called from the actual
model response. To inspect just the opening turn:

```bash
uv run python trivia_agent.py --ask-key --once
```

Check setup without a model key or external trivia requests:

```bash
uv run python trivia_agent.py --smoke
```

After typing `stop` (or an empty answer), choose Good, Bad, or Skip from the
feedback menu. Good records `feedback=1`; Bad records `feedback=-1`; Skip or
cancelling the menu records nothing. Feedback is logged while `trivia_session`
is still active, so the feedback event shares the agent runs' trace and has
the session span as its parent. Smoke runs do not ask for feedback.

Count feedback and check its session parentage:

```bash
uv run python feedback_counts.py
```

Use `--since` with an ISO timestamp to change the query window. When feedback
is collected outside the active span (for example in a separate request),
capture the session with `logfire.get_context()` and log the event inside
`with logfire.attach_context(session_context):` to join the same trace.

Replay the completed grouped Science & Nature session and calculate cost:

```bash
uv run python replay_session.py
```

This downloads trace `01a169edd60318b8442822db1883aea3` using the local
Logfire read token and writes an `AgentRunResult` to the ignored
`.logfire/replayed_session.json`. The local `trace_replay/` helper handles both
`agent run` and `invoke_agent <name>` spans. It sums usage across every agent
turn, excludes nested model usage from that sum, and keeps the final full
conversation. This is a local implementation, not the lesson's source copy.
The replay does not make new model requests.

The six-turn session used 10,467 input tokens (7,736 cached, 2,731 uncached)
and 1,772 output tokens. Using the supplied GLM Standard rates of $0.15/M
uncached input, $0.03/M cached input, and $0.50/M output gives approximately
**$0.00152773**. Using the homework's GPT-4o-mini rates as a comparison gives
**$0.00263325**. These are token-based estimates, not billing statements.

Test the category tool directly (no model API key required):

```bash
uv run python -c "from tools.trivia_tools import TriviaTools; print(TriviaTools().get_categories())"
```

Fetch two easy general knowledge questions:

```bash
uv run python -c "from tools.trivia_tools import TriviaTools; print(TriviaTools().get_questions(2, 9, 'easy'))"
```

Open Trivia DB limits question requests to one per five seconds. The tools use
a 15-second HTTP timeout and report HTTP errors and API response codes.

```bash
uv sync
uv run python main.py --smoke
```

The smoke command uses Pydantic AI's deterministic TestModel, makes no paid model
requests, and sends agent traces to Logfire. Local Logfire credentials are stored
in the ignored `.logfire/` directory.

For a real model, set `PYDANTIC_AI_MODEL` to a `provider:model` identifier and
set that provider's API key in your shell, then run:

```bash
uv run python main.py "Quiz me with 3 easy general knowledge questions"
```

For example, OpenAI uses `OPENAI_API_KEY`. The Pydantic AI Gateway uses
`PYDANTIC_AI_GATEWAY_API_KEY` and `gateway/provider:model` identifiers.
Keep credentials out of source control. Agent prompts and responses are captured
by Logfire instrumentation.

Traces: https://logfire-us.pydantic.dev/micah-sircularity/demo-test/live

To connect another checkout, run `uv run logfire auth`, followed by
`uv run logfire projects use demo-test --org micah-sircularity`.
Deployments can supply `LOGFIRE_TOKEN` through their secret manager.
