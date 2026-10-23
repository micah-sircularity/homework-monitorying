"""Collect optional end-of-session feedback."""

import questionary


def ask_feedback() -> int | None:
    result = questionary.select(
        "How was the trivia session?",
        choices=["👍 Good", "👎 Bad", "Skip"],
    ).ask()
    if result is None or result == "Skip":
        return None
    return 1 if "Good" in result else -1
