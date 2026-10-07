from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


PRICING_AS_OF = "2026-10-07"

# Standard processing, short-context text-token prices in USD
# per 1M tokens.
MODEL_PRICING_USD_PER_MILLION = {
    "gpt-5.6-luna": {
        "input": 0.20,
        "cached_input": 0.02,
        "cache_write_input": 0.25,
        "output": 1.20,
    },
}


@dataclass(frozen=True)
class LLMRunMetrics:
    model: str
    latency_seconds: float
    llm_requests: int
    tool_calls: int
    input_tokens: int
    cached_input_tokens: int
    cache_write_input_tokens: int
    output_tokens: int
    reasoning_tokens: int
    total_tokens: int
    cache_hit_rate: float
    estimated_cost_usd: float | None
    pricing_as_of: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _detail_value(details: Any, field_name: str) -> int:
    if details is None:
        return 0

    value = getattr(details, field_name, 0)

    if value is None:
        return 0

    return int(value)


def estimate_token_cost_usd(
    *,
    model: str,
    input_tokens: int,
    cached_input_tokens: int,
    cache_write_input_tokens: int,
    output_tokens: int,
) -> float | None:
    pricing = MODEL_PRICING_USD_PER_MILLION.get(
        model
    )

    if pricing is None:
        return None

    uncached_input_tokens = max(
        input_tokens
        - cached_input_tokens
        - cache_write_input_tokens,
        0,
    )

    return (
        uncached_input_tokens * pricing["input"]
        + cached_input_tokens * pricing["cached_input"]
        + cache_write_input_tokens
        * pricing["cache_write_input"]
        + output_tokens * pricing["output"]
    ) / 1_000_000


def collect_run_metrics(
    *,
    result: Any,
    latency_seconds: float,
    model: str,
) -> LLMRunMetrics:
    usage = result.context_wrapper.usage

    cached_input_tokens = _detail_value(
        usage.input_tokens_details,
        "cached_tokens",
    )
    cache_write_input_tokens = _detail_value(
        usage.input_tokens_details,
        "cache_write_tokens",
    )
    reasoning_tokens = _detail_value(
        usage.output_tokens_details,
        "reasoning_tokens",
    )

    tool_calls = sum(
        1
        for item in result.new_items
        if getattr(item, "type", None) == "tool_call_item"
    )

    cache_hit_rate = (
        cached_input_tokens / usage.input_tokens
        if usage.input_tokens
        else 0.0
    )

    estimated_cost_usd = estimate_token_cost_usd(
        model=model,
        input_tokens=usage.input_tokens,
        cached_input_tokens=cached_input_tokens,
        cache_write_input_tokens=cache_write_input_tokens,
        output_tokens=usage.output_tokens,
    )

    return LLMRunMetrics(
        model=model,
        latency_seconds=latency_seconds,
        llm_requests=usage.requests,
        tool_calls=tool_calls,
        input_tokens=usage.input_tokens,
        cached_input_tokens=cached_input_tokens,
        cache_write_input_tokens=cache_write_input_tokens,
        output_tokens=usage.output_tokens,
        reasoning_tokens=reasoning_tokens,
        total_tokens=usage.total_tokens,
        cache_hit_rate=cache_hit_rate,
        estimated_cost_usd=estimated_cost_usd,
        pricing_as_of=(
            PRICING_AS_OF
            if estimated_cost_usd is not None
            else None
        ),
    )
