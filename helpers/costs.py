"""Approximate USD costs using the homework's supplied per-million rates."""

MODEL_PRICES = {
    "gpt-4o-mini": {"input": 0.15, "cached_input": 0.15, "output": 0.60},
    "glm-5p3-flash": {"input": 0.15, "cached_input": 0.03, "output": 0.50},
}


def calculate_cost(model_name: str, input_tokens: int, output_tokens: int, cached_input_tokens: int = 0) -> float:
    """Input tokens include cache hits; charge each input token only once."""
    if min(input_tokens, output_tokens, cached_input_tokens) < 0 or cached_input_tokens > input_tokens:
        raise ValueError("Token counts must be nonnegative and cache hits cannot exceed input")
    prices = MODEL_PRICES[model_name.lower()]
    return (
        (input_tokens - cached_input_tokens) * prices["input"]
        + cached_input_tokens * prices["cached_input"]
        + output_tokens * prices["output"]
    ) / 1_000_000
