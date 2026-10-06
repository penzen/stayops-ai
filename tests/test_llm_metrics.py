from types import SimpleNamespace

from backend.observability.llm_metrics import collect_run_metrics


def test_collect_run_metrics_reads_sdk_usage_details():
    usage = SimpleNamespace(
        requests=3,
        input_tokens=12_000,
        output_tokens=600,
        total_tokens=12_600,
        input_tokens_details=SimpleNamespace(
            cached_tokens=8_000,
            cache_write_tokens=2_000,
        ),
        output_tokens_details=SimpleNamespace(
            reasoning_tokens=100,
        ),
    )

    result = SimpleNamespace(
        context_wrapper=SimpleNamespace(
            usage=usage,
        ),
        new_items=[
            SimpleNamespace(
                type="tool_call_item"
            ),
            SimpleNamespace(
                type="tool_call_output_item"
            ),
            SimpleNamespace(
                type="tool_call_item"
            ),
        ],
    )

    metrics = collect_run_metrics(
        result=result,
        latency_seconds=4.25,
    )

    assert metrics.latency_seconds == 4.25
    assert metrics.llm_requests == 3
    assert metrics.tool_calls == 2
    assert metrics.cached_input_tokens == 8_000
    assert metrics.cache_write_input_tokens == 2_000
    assert metrics.reasoning_tokens == 100
    assert metrics.cache_hit_rate == (
        8_000 / 12_000
    )
