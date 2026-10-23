"""HTTP access to Open Trivia DB."""

import requests


def get_trivia_data(endpoint: str, params: dict | None = None) -> dict:
    """Fetch JSON with a bounded wait and surface HTTP/API errors."""
    response = requests.get(
        f"https://opentdb.com/{endpoint}", params=params, timeout=15
    )
    response.raise_for_status()
    data = response.json()
    code = data.get("response_code", 0)
    if code:
        messages = {
            1: "Not enough questions match this category and difficulty. Try fewer questions.",
            2: "Open Trivia DB rejected the request parameters.",
            3: "The session token was not found.",
            4: "The session token has exhausted its questions.",
            5: "Open Trivia DB rate limit reached. Wait at least 5 seconds before retrying.",
        }
        raise ValueError(messages.get(code, f"Open Trivia DB returned response code {code}."))
    return data
