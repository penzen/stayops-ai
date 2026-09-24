import asyncio
import json
import os
import sqlite3
from collections.abc import Mapping

from backend.domain.enums import SenderType

from backend.services.db_fixture import reset_eval_database

from backend.services.cases import (
    get_open_cases_for_booking,
)

from backend.services.messages import (
    send_message,
    get_booking_messages,
)

from backend.agent.guest_agent import run_guest_agent
from backend.evals.scenarios import EVALUATION_SCENARIOS
from backend.evals.judge import judge_agent_response


def raw_field(item, field_name):
    """
    Safely read a field from an SDK raw_item.

    raw_item may be either:
    - a dictionary-like mapping
    - an SDK response object
    """

    raw_item = item.raw_item

    if isinstance(raw_item, Mapping):
        return raw_item.get(field_name)

    return getattr(raw_item, field_name, None)


def extract_tool_calls(result):
    """
    Extract tool calls from result.new_items.
    """

    tool_calls = []

    for item in result.new_items:

        if getattr(item, "type", None) != "tool_call_item":
            continue

        tool_name = getattr(item, "tool_name", None)

        arguments = raw_field(
            item,
            "arguments",
        )

        # Arguments usually arrive as JSON text.
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                pass

        tool_calls.append(
            {
                "tool_name": tool_name,
                "arguments": arguments,
                "call_id": getattr(
                    item,
                    "call_id",
                    None,
                ),
            }
        )

    return tool_calls

def extract_tool_outputs(result):
    """
    Extract tool outputs and associate them with their
    original tool names using call_id.
    """

    tool_calls = extract_tool_calls(result)

    tool_names_by_call_id = {
        call["call_id"]: call["tool_name"]
        for call in tool_calls
    }

    tool_outputs = []

    for item in result.new_items:

        if (
            getattr(item, "type", None)
            != "tool_call_output_item"
        ):
            continue

        call_id = getattr(
            item,
            "call_id",
            None,
        )

        output = getattr(
            item,
            "output",
            None,
        )

        # Fall back to raw_item if needed.
        if output is None:
            output = raw_field(
                item,
                "output",
            )

        # Some MCP outputs may arrive as JSON text.
        if isinstance(output, str):
            try:
                output = json.loads(output)
            except json.JSONDecodeError:
                pass

        tool_outputs.append(
            {
                "tool_name": (
                    tool_names_by_call_id.get(
                        call_id
                    )
                ),
                "call_id": call_id,
                "output": output,
            }
        )

    return tool_outputs


def output_contains(
    output,
    expected_text,
):
    """
    Search a tool output regardless of whether it is a
    dictionary, list, JSON value, or plain string.
    """

    output_text = json.dumps(
        output,
        ensure_ascii=False,
        default=str,
    ).lower()

    return expected_text.lower() in output_text



def check_database_state(
    scenario,
    db_path,
):
    """
    Verify that expected operational state actually exists
    in the evaluation database after the agent run.
    """

    failures = []

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row

    try:
        booking_id = scenario["booking_id"]

        # -----------------------------------------------------
        # EXPECTED ESCALATION
        # -----------------------------------------------------

        if scenario.get("expected_escalation"):
            expected_category = scenario["expected_category"]

            escalation = connection.execute(
                """
                SELECT *
                FROM escalations
                WHERE booking_id = ?
                  AND category = ?
                  AND status = 'open'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (
                    booking_id,
                    expected_category,
                ),
            ).fetchone()

            if escalation is None:
                failures.append(
                    "Expected open database escalation "
                    f"with category '{expected_category}' "
                    "was not found."
                )

        # -----------------------------------------------------
        # EXPECTED TASK
        # -----------------------------------------------------

        expected_task_category = scenario.get(
            "expected_task_category"
        )

        if expected_task_category:
            task = connection.execute(
                """
                SELECT *
                FROM tasks
                WHERE booking_id = ?
                  AND category = ?
                  AND task_status = 'open'
                ORDER BY task_date DESC
                LIMIT 1
                """,
                (
                    booking_id,
                    expected_task_category,
                ),
            ).fetchone()

            if task is None:
                failures.append(
                    "Expected open database task "
                    f"with category "
                    f"'{expected_task_category}' "
                    "was not found."
                )

    finally:
        connection.close()

    return failures

def evaluate_scenario(
    scenario,
    result,
    db_path,
):
    """
    Perform deterministic checks against an agent run.
    """

    failures = []

    final_output = str(
        result.final_output or ""
    )

    final_output_lower = final_output.lower()

    tool_calls = extract_tool_calls(result)

    # ---------------------------------------------------------
    # KNOWLEDGE RETRIEVAL
    # ---------------------------------------------------------

    knowledge_calls = [
        call
        for call in tool_calls
        if call["tool_name"] == "qdrant-find"
    ]

    # ---------------------------------------------------------
    # APPROVED OPERATIONAL GUIDANCE
    # ---------------------------------------------------------

    playbook_calls = [
        call
        for call in tool_calls
        if call["tool_name"]
        == "lookup_operational_playbook"
    ]

    knowledge_calls = [
        call
        for call in tool_calls
        if call["tool_name"] == "qdrant-find"
    ]

    if not playbook_calls and not knowledge_calls:
        failures.append(
            "Agent did not retrieve approved operational "
            "guidance through either the structured playbook "
            "or operational knowledge base."
        )

    # ---------------------------------------------------------
    # ESCALATION
    # ---------------------------------------------------------

    if scenario.get("expected_escalation"):

        escalation_calls = [
            call
            for call in tool_calls
            if call["tool_name"]
            == "ensure_human_escalation"
        ]

        if not escalation_calls:
            failures.append(
                "Expected human escalation was not attempted."
            )

        else:
            expected_category = scenario.get(
                "expected_category"
            )

            matching_category = False

            for call in escalation_calls:

                arguments = call["arguments"]

                if not isinstance(
                    arguments,
                    dict,
                ):
                    continue

                if (
                    arguments.get("category")
                    == expected_category
                ):
                    matching_category = True
                    break

            if not matching_category:
                failures.append(
                    "Human escalation used the wrong "
                    f"category. Expected "
                    f"'{expected_category}'."
                )

    # ---------------------------------------------------------
    # FORBIDDEN RESPONSE CONTENT
    # ---------------------------------------------------------

    for phrase in scenario.get(
        "forbidden_phrases",
        [],
    ):
        if phrase.lower() in final_output_lower:
            failures.append(
                f"Forbidden phrase found: {phrase}"
            )

    # ---------------------------------------------------------
    # RESULT
    # ---------------------------------------------------------
    database_failures = check_database_state(
        scenario,
        db_path,
    )

    failures.extend(database_failures)

    passed = len(failures) == 0

    return {
        "name": scenario["name"],
        "passed": passed,
        "failures": failures,
        "final_output": final_output,
        "tool_calls": tool_calls,
    }


async def run_eval_turn(
    *,
    guest_id: str,
    booking_id: str,
    message: str,
    scenario_name: str,
    db_path,
):
    """
    Run one evaluation turn using the same multi-turn context
    flow as the production API.

    The evaluation database is temporarily exposed to the
    service layer through STAYOPS_DB_PATH so Cases and messages
    are loaded from the correct database.
    """

    previous_db_path = os.environ.get(
        "STAYOPS_DB_PATH"
    )

    os.environ["STAYOPS_DB_PATH"] = str(
        db_path
    )

    try:
        # Load context BEFORE storing the current guest message,
        # matching the production API behavior.
        open_cases = get_open_cases_for_booking(
            booking_id
        )

        recent_messages = get_booking_messages(
            booking_id
        )[-6:]

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
            recent_messages=recent_messages,
        )

        send_message(
            booking_id=booking_id,
            guest_id=guest_id,
            sender_type=SenderType.AGENT,
            message_text=str(
                result.final_output or ""
            ),
        )

        return result

    finally:
        if previous_db_path is None:
            os.environ.pop(
                "STAYOPS_DB_PATH",
                None,
            )
        else:
            os.environ["STAYOPS_DB_PATH"] = (
                previous_db_path
            )

async def main():

    results = []

    print("\nSTAYOPS EVALUATION SUITE")
    print("=" * 70)

    # Run sequentially because local Qdrant uses
    # the same on-disk database.

    for scenario in EVALUATION_SCENARIOS:

        print(
            f"\nRunning: {scenario['name']}"
        )

        # Give every evaluation scenario a clean operational state.
        eval_db_path = reset_eval_database()

        result = await run_guest_agent(
            guest_id=scenario["guest_id"],
            booking_id=scenario["booking_id"],
            message=scenario["message"],
            scenario_name=(
                f"eval_{scenario['name']}"
            ),
            db_path=eval_db_path,
        )
         # ---------------------------------------------------------
         # DETERMINISTIC EVALUATION
         # ---------------------------------------------------------

        evaluation = evaluate_scenario(
            scenario,
            result,
            eval_db_path,
        )

        # ---------------------------------------------------------
        # LLM-AS-JUDGE EVALUATION
        # ---------------------------------------------------------

        tool_outputs = extract_tool_outputs(result)

        judge_result = await judge_agent_response(
            scenario=scenario,
            final_output=evaluation["final_output"],
            tool_calls=evaluation["tool_calls"],
            tool_outputs=tool_outputs,
        )
        
        evaluation["tool_outputs"] = tool_outputs
        evaluation["judge"] = judge_result
        results.append(evaluation)

         # ---------------------------------------------------------
         # DETERMINISTIC RESULT
         # ---------------------------------------------------------
        
        if evaluation["passed"]:
            print("PASS")
        else:
            print("FAIL")

            for failure in evaluation[
                "failures"
            ]:
                print(f"  - {failure}")

        print(
            f"Response: "
            f"{evaluation['final_output']}"
        )
         # ---------------------------------------------------------
         # JUDGE RESULT
         # ---------------------------------------------------------

        judge = judge_result["evaluation"]

        print(
            f"Judge: "
            f"{'PASS' if judge_result['passed'] else 'FAIL'}"
        )

        print(
            "Judge scores: "
            f"groundedness={judge.groundedness}, "
            f"sop={judge.sop_adherence}, "
            f"safety={judge.safety}, "
            f"handoff={judge.handoff_quality}, "
            f"helpfulness={judge.helpfulness}"
        )

        if judge.concerns:
            print("Judge concerns:")

            for concern in judge.concerns:
                print(f"  - {concern}")


       # ---------------------------------------------------------
    # IDEMPOTENCY EVALUATION
    # ---------------------------------------------------------

    idempotency_passed = await run_idempotency_eval()
    multiturn_passed = (
        await run_multiturn_case_reuse_eval()
    )



    # ---------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------

    deterministic_passed = sum(
        result["passed"]
        for result in results
    )

    judge_passed = sum(
        result["judge"]["passed"]
        for result in results
    )

    overall_scenario_passed = sum(
        result["passed"]
        and result["judge"]["passed"]
        for result in results
    )

    scenario_count = len(results)

    suite_passed = (
        overall_scenario_passed == scenario_count
        and idempotency_passed
        and multiturn_passed
    )

    print(
    f"Multi-turn Case reuse:   "
    f"{'PASS' if multiturn_passed else 'FAIL'}"
    )

    print("\n" + "=" * 70)
    print("EVALUATION SUMMARY")
    print("=" * 70)

    print(
        f"Deterministic scenarios: "
        f"{deterministic_passed}/{scenario_count}"
    )

    print(
        f"LLM judge scenarios:     "
        f"{judge_passed}/{scenario_count}"
    )

    print(
        f"Overall scenarios:       "
        f"{overall_scenario_passed}/{scenario_count}"
    )

    print(
        f"Idempotency:             "
        f"{'PASS' if idempotency_passed else 'FAIL'}"
    )
    print(
        f"Multi-turn Case reuse:   "
        f"{'PASS' if multiturn_passed else 'FAIL'}"
    )

    print(
        f"Overall suite:           "
        f"{'PASS' if suite_passed else 'FAIL'}"
    )
    

async def run_multiturn_case_reuse_eval():
    """
    Verify that an ambiguous follow-up continues the same
    operational Case instead of creating duplicate Cases,
    tasks, or escalations.
    """

    print("\nRunning: heating_multiturn_case_reuse")

    guest_id = "gst_2631"
    booking_id = "book_demo_current_001"

    eval_db_path = reset_eval_database()

    # ---------------------------------------------------------
    # TURN 1
    # ---------------------------------------------------------

    await run_eval_turn(
        guest_id=guest_id,
        booking_id=booking_id,
        message=(
            "The heating is broken and the apartment "
            "is getting cold."
        ),
        scenario_name=(
            "eval_heating_multiturn_first"
        ),
        db_path=eval_db_path,
    )

    # ---------------------------------------------------------
    # TURN 2
    # ---------------------------------------------------------

    second_result = await run_eval_turn(
        guest_id=guest_id,
        booking_id=booking_id,
        message="Let's fix it.",
        scenario_name=(
            "eval_heating_multiturn_second"
        ),
        db_path=eval_db_path,
    )

    second_tool_calls = extract_tool_calls(
        second_result
    )
    # Retrieving deep Case context is useful when needed,
    # but is not required on every follow-up because the
    # agent already receives active Cases and recent conversation
    # as structured pre-run context.

    case_context_retrieved = any(
        call["tool_name"]
        == "lookup_case_context"
        for call in second_tool_calls
    )

    # ---------------------------------------------------------
    # VERIFY DATABASE STATE
    # ---------------------------------------------------------

    connection = sqlite3.connect(
        eval_db_path
    )

    connection.row_factory = sqlite3.Row

    try:
        cases = connection.execute(
            """
            SELECT *
            FROM cases
            WHERE booking_id = ?
              AND category = 'heating'
              AND status != 'resolved'
            """,
            (booking_id,),
        ).fetchall()

        tasks = connection.execute(
            """
            SELECT *
            FROM tasks
            WHERE booking_id = ?
              AND category = 'heating'
              AND task_status = 'open'
            """,
            (booking_id,),
        ).fetchall()

        escalations = connection.execute(
            """
            SELECT *
            FROM escalations
            WHERE booking_id = ?
              AND category = 'heating'
              AND status = 'open'
            """,
            (booking_id,),
        ).fetchall()

    finally:
        connection.close()

    exactly_one_case = len(cases) == 1
    exactly_one_task = len(tasks) == 1
    exactly_one_escalation = (
        len(escalations) == 1
    )

    same_case_ownership = False

    if (
        exactly_one_case
        and exactly_one_task
        and exactly_one_escalation
    ):
        case_id = cases[0]["case_id"]

        same_case_ownership = (
            tasks[0]["case_id"] == case_id
            and escalations[0]["case_id"]
            == case_id
        )

    passed = (
        exactly_one_case
        and exactly_one_task
        and exactly_one_escalation
        and same_case_ownership
    )

    print(
        "Case context retrieved: "
        f"{case_context_retrieved}"
    )

    print(
        f"Active heating Cases: "
        f"{len(cases)}"
    )

    print(
        f"Open heating tasks: "
        f"{len(tasks)}"
    )

    print(
        f"Open heating escalations: "
        f"{len(escalations)}"
    )

    print(
        "Same Case ownership: "
        f"{same_case_ownership}"
    )

    print(
        "PASS"
        if passed
        else "FAIL"
    )

    return passed
    


async def run_idempotency_eval():
    """
    Run the same plumbing scenario twice against the same
    evaluation database and verify that duplicate operational
    records are not created.
    """

    print("\nRunning: plumbing_idempotency")

    scenario = next(
        scenario
        for scenario in EVALUATION_SCENARIOS
        if scenario["name"] == "plumbing_worsening_leak"
    )

    # Reset ONCE.
    # Both runs intentionally share the same database.
    eval_db_path = reset_eval_database()

    # First run
    first_result = await run_eval_turn(
        guest_id=scenario["guest_id"],
        booking_id=scenario["booking_id"],
        message=scenario["message"],
        scenario_name="eval_plumbing_idempotency_first",
        db_path=eval_db_path,
    )

    second_result = await run_eval_turn(
        guest_id=scenario["guest_id"],
        booking_id=scenario["booking_id"],
        message=scenario["message"],
        scenario_name="eval_plumbing_idempotency_second",
        db_path=eval_db_path,
    )

    second_tool_outputs = extract_tool_outputs(
        second_result
    )

    task_reused = any(
        output["tool_name"]
        == "ensure_operations_task"
        and output_contains(
            output["output"],
            "existing_open_task",
        )
        for output in second_tool_outputs
    )

    escalation_reused = any(
        output["tool_name"]
        == "ensure_human_escalation"
        and output_contains(
            output["output"],
            "existing_open_escalation",
        )
        for output in second_tool_outputs
    )

    connection = sqlite3.connect(eval_db_path)

    try:
        task_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM tasks
            WHERE booking_id = ?
              AND category = 'plumbing'
              AND task_status = 'open'
            """,
            (scenario["booking_id"],),
        ).fetchone()[0]

        escalation_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM escalations
            WHERE booking_id = ?
              AND category = 'plumbing'
              AND status = 'open'
            """,
            (scenario["booking_id"],),
        ).fetchone()[0]

    finally:
        connection.close()

    # Tool-level reuse is useful observability when the agent
    # chooses to call the idempotent creation tools again.
    #
    # It is not required for correctness because the agent may
    # recognize existing operational work from Case/context and
    # correctly avoid calling those tools at all.
    #
    # The deterministic requirement is that repeating the issue
    # does not create duplicate operational records.

    passed = (
        task_count == 1
        and escalation_count == 1
    )
    print(
        f"Task tool reported reuse: "
        f"{task_reused}")

    print(
        f"Escalation tool reported reuse: "
        f"{escalation_reused}")

    if passed:
        print("PASS")
    else:
        print("FAIL")

    print(f"Open plumbing tasks: {task_count}")
    print(
        f"Open plumbing escalations: "
        f"{escalation_count}"
    )

    return passed

if __name__ == "__main__":
    asyncio.run(main())