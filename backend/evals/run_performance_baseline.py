from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import time
from collections import Counter
from pathlib import Path

from agents.mcp import MCPServer, MCPServerManager

from backend.agent.guest_agent import (
    create_knowledge_mcp_server,
    create_operations_mcp_server,
    run_guest_agent,
)
from backend.domain.enums import SenderType
from backend.evals.run_evals import evaluate_scenario
from backend.evals.scenarios import EVALUATION_SCENARIOS
from backend.observability.llm_metrics import collect_run_metrics
from backend.services.cases import (
    get_open_cases_for_booking,
    get_recent_cases_for_booking,
)
from backend.services.db_fixture import reset_eval_database
from backend.services.messages import (
    get_booking_messages,
    send_message,
)
from backend.services.guests import get_guest
from backend.services.reservations import get_reservation
from backend.services.properties import get_property


def mean(values: list[float | int]) -> float:
    return statistics.fmean(values) if values else 0.0


async def run_persistent_eval_turn(
    *,
    guest_id: str,
    booking_id: str,
    message: str,
    scenario_name: str,
    db_path: Path,
    mcp_servers: list[MCPServer],
):
    previous_db_path = os.environ.get("STAYOPS_DB_PATH")
    os.environ["STAYOPS_DB_PATH"] = str(db_path)

    try:
        guest = get_guest(guest_id)
        reservation = get_reservation(booking_id)

        property_data = None

        if reservation is not None:
            property_id = reservation.get("property_id")

            if property_id:
                property_data = get_property(property_id)

        open_cases = get_open_cases_for_booking(booking_id)
        recent_cases = get_recent_cases_for_booking(
            booking_id,
            limit=5,
        )
        recent_messages = get_booking_messages(booking_id)[-6:]

        send_message(
            booking_id=booking_id,
            guest_id=guest_id,
            sender_type=SenderType.GUEST,
            message_text=message,
        )

        result = await run_guest_agent(
            guest_id=guest_id,
            booking_id=booking_id,
            message=message,
            scenario_name=scenario_name,
            show_tools=False,
            db_path=db_path,
            open_cases=open_cases,
            recent_cases=recent_cases,
            recent_messages=recent_messages,
            mcp_servers=mcp_servers,
            guest=guest,
            reservation=reservation,
            property_data=property_data,
        )

        send_message(
            booking_id=booking_id,
            guest_id=guest_id,
            sender_type=SenderType.AGENT,
            message_text=str(result.final_output or ""),
        )

        return result

    finally:
        if previous_db_path is None:
            os.environ.pop("STAYOPS_DB_PATH", None)
        else:
            os.environ["STAYOPS_DB_PATH"] = previous_db_path


def combine_tool_breakdowns(
    runs: list[dict],
) -> dict[str, int]:
    counter: Counter[str] = Counter()

    for run in runs:
        counter.update(
            run.get("tool_call_breakdown", {})
        )

    return dict(
        sorted(
            counter.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def summarize_scenario(
    *,
    scenario_name: str,
    runs: list[dict],
) -> dict:
    passed_runs = sum(
        1
        for run in runs
        if run["passed"]
    )

    input_tokens = sum(
        run["metrics"]["input_tokens"]
        for run in runs
    )
    cached_tokens = sum(
        run["metrics"]["cached_input_tokens"]
        for run in runs
    )

    return {
        "scenario": scenario_name,
        "runs": len(runs),
        "pass_rate": (
            passed_runs / len(runs)
            if runs
            else 0.0
        ),
        "avg_latency_seconds": mean(
            [
                run["metrics"]["latency_seconds"]
                for run in runs
            ]
        ),
        "avg_llm_requests": mean(
            [
                run["metrics"]["llm_requests"]
                for run in runs
            ]
        ),
        "avg_tool_calls": mean(
            [
                run["metrics"]["tool_calls"]
                for run in runs
            ]
        ),
        "avg_input_tokens": mean(
            [
                run["metrics"]["input_tokens"]
                for run in runs
            ]
        ),
        "avg_output_tokens": mean(
            [
                run["metrics"]["output_tokens"]
                for run in runs
            ]
        ),
        "cache_hit_rate": (
            cached_tokens / input_tokens
            if input_tokens
            else 0.0
        ),
        "avg_cache_write_tokens": mean(
            [
                run["metrics"]["cache_write_input_tokens"]
                for run in runs
            ]
        ),
        "tool_call_breakdown": combine_tool_breakdowns(
            runs
        ),
    }


def print_tool_breakdown(
    *,
    title: str,
    breakdown: dict[str, int],
    runs: int,
) -> None:
    print(f"\n{title}")

    if not breakdown:
        print("  No tool calls recorded.")
        return

    longest_name = max(len(name) for name in breakdown)

    for tool_name, total_calls in breakdown.items():
        avg_per_run = (
            total_calls / runs
            if runs
            else 0.0
        )

        print(
            f"  {tool_name:<{longest_name}}  "
            f"{total_calls:>3} total  "
            f"{avg_per_run:>5.2f}/run"
        )


def print_summary(
    summaries: list[dict],
    *,
    raw_runs: list[dict],
    mcp_startup_seconds: float,
) -> None:
    print("\n" + "=" * 106)
    print("STAYOPS PERFORMANCE - PERSISTENT MCP")
    print("=" * 106)
    print(
        f"One-time MCP startup: "
        f"{mcp_startup_seconds:.2f}s"
    )
    print(
        "Per-chat latency below excludes that one-time "
        "application startup cost."
    )
    print(
        "Quality gate: deterministic StayOps scenario checks. "
        "The existing full eval suite remains unchanged."
    )
    print()

    header = (
        f"{'Scenario':<28}"
        f"{'N':>4}"
        f"{'Pass':>8}"
        f"{'Latency':>11}"
        f"{'LLM':>7}"
        f"{'Tools':>8}"
        f"{'In tok':>10}"
        f"{'Out tok':>10}"
        f"{'Cache':>9}"
        f"{'Writes':>11}"
    )
    print(header)
    print("-" * len(header))

    for summary in summaries:
        print(
            f"{summary['scenario']:<28}"
            f"{summary['runs']:>4}"
            f"{summary['pass_rate']:>7.0%}"
            f"{summary['avg_latency_seconds']:>10.2f}s"
            f"{summary['avg_llm_requests']:>7.2f}"
            f"{summary['avg_tool_calls']:>8.2f}"
            f"{summary['avg_input_tokens']:>10.0f}"
            f"{summary['avg_output_tokens']:>10.0f}"
            f"{summary['cache_hit_rate']:>8.1%}"
            f"{summary['avg_cache_write_tokens']:>11.0f}"
        )

    print("\n" + "=" * 106)
    print("TOOL CALL BREAKDOWN")
    print("=" * 106)

    for summary in summaries:
        print_tool_breakdown(
            title=summary["scenario"],
            breakdown=summary["tool_call_breakdown"],
            runs=summary["runs"],
        )

    print_tool_breakdown(
        title="OVERALL",
        breakdown=combine_tool_breakdowns(raw_runs),
        runs=len(raw_runs),
    )


async def run_benchmark(
    *,
    runs_per_scenario: int,
) -> dict:
    benchmark_db_path = reset_eval_database()

    servers = [
        create_operations_mcp_server(
            benchmark_db_path
        ),
        create_knowledge_mcp_server(),
    ]

    manager = MCPServerManager(
        servers,
        strict=True,
        connect_in_parallel=True,
        connect_timeout_seconds=180.0,
        cleanup_timeout_seconds=30.0,
    )

    startup_started = time.perf_counter()

    async with manager:
        mcp_startup_seconds = (
            time.perf_counter() - startup_started
        )

        raw_runs: list[dict] = []
        summaries: list[dict] = []

        for scenario in EVALUATION_SCENARIOS:
            scenario_runs: list[dict] = []

            for run_number in range(
                1,
                runs_per_scenario + 1,
            ):
                print(
                    f"Running {scenario['name']} "
                    f"({run_number}/{runs_per_scenario})"
                )

                eval_db_path = reset_eval_database()

                if eval_db_path != benchmark_db_path:
                    raise RuntimeError(
                        "Performance benchmark expected a "
                        "stable evaluation database path."
                    )

                started = time.perf_counter()

                result = await run_persistent_eval_turn(
                    guest_id=scenario["guest_id"],
                    booking_id=scenario["booking_id"],
                    message=scenario["message"],
                    scenario_name=(
                        "persistent_mcp_"
                        f"{scenario['name']}_"
                        f"{run_number}"
                    ),
                    db_path=eval_db_path,
                    mcp_servers=manager.active_servers,
                )

                latency_seconds = (
                    time.perf_counter() - started
                )

                evaluation = evaluate_scenario(
                    scenario,
                    result,
                    eval_db_path,
                )

                metrics = collect_run_metrics(
                    result=result,
                    latency_seconds=latency_seconds,
                )

                tool_names = [
                    call["tool_name"]
                    for call in evaluation["tool_calls"]
                    if call.get("tool_name")
                ]

                run_record = {
                    "scenario": scenario["name"],
                    "run": run_number,
                    "passed": evaluation["passed"],
                    "failures": evaluation["failures"],
                    "metrics": metrics.to_dict(),
                    "tool_call_breakdown": dict(
                        Counter(tool_names)
                    ),
                }

                scenario_runs.append(run_record)
                raw_runs.append(run_record)

            summaries.append(
                summarize_scenario(
                    scenario_name=scenario["name"],
                    runs=scenario_runs,
                )
            )

        return {
            "mode": "persistent_mcp",
            "mcp_startup_seconds": mcp_startup_seconds,
            "runs_per_scenario": runs_per_scenario,
            "summaries": summaries,
            "overall_tool_call_breakdown": (
                combine_tool_breakdowns(raw_runs)
            ),
            "runs": raw_runs,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Measure StayOps with long-lived MCP servers "
            "and report tool-call frequency."
        )
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=3,
        help="Runs per evaluation scenario (default: 3).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional JSON output path.",
    )

    args = parser.parse_args()

    if args.runs < 1:
        parser.error("--runs must be at least 1")

    return args


async def main() -> None:
    args = parse_args()

    benchmark = await run_benchmark(
        runs_per_scenario=args.runs,
    )

    print_summary(
        benchmark["summaries"],
        raw_runs=benchmark["runs"],
        mcp_startup_seconds=benchmark[
            "mcp_startup_seconds"
        ],
    )

    if args.output is not None:
        args.output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        args.output.write_text(
            json.dumps(
                benchmark,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        print(
            f"\nSaved benchmark JSON to "
            f"{args.output}"
        )


if __name__ == "__main__":
    asyncio.run(main())
