from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class LLMRunMetrics:
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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _detail_value(details: Any, field_name: str) -> int:
    if details is None:
        return 0

    value = getattr(details, field_name, 0)

    if value is None:
        return 0

    return int(value)


def collect_run_metrics(
    *,
    result: Any,
    latency_seconds: float,
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

    return LLMRunMetrics(
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
    )
