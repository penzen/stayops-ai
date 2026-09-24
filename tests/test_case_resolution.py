import pytest

from backend.services.cases import (
    ensure_case,
    get_case,
    resolve_case_if_ready,
)
from backend.services.tasks import (
    create_task_if_missing,
    complete_task,
)
from backend.services.escalations import (
    create_escalation_if_missing,
    resolve_escalation,
)


PROPERTY_ID = "prop_15"
BOOKING_ID = "book_demo_current_001"


def test_case_resolution_blocked_while_work_is_open(test_db):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating is broken.",
    )

    case_id = case_result["case"]["case_id"]

    create_task_if_missing(
        property_id=PROPERTY_ID,
        booking_id=BOOKING_ID,
        category="heating",
        title="Investigate heating failure",
        case_id=case_id,
    )

    create_escalation_if_missing(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        reason="Human intervention required.",
        priority="high",
        case_id=case_id,
    )

    result = resolve_case_if_ready(case_id)

    assert result["resolved"] is False
    assert result["reason"] == "unresolved_operational_work"

    assert result["open_tasks"] == 1
    assert result["open_escalations"] == 1

    case = get_case(case_id)

    assert case is not None
    assert case["status"] != "resolved"
    assert case["resolved_at"] is None


def test_case_resolves_after_operational_work_finishes(test_db):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating is broken.",
    )

    case_id = case_result["case"]["case_id"]

    task_result = create_task_if_missing(
        property_id=PROPERTY_ID,
        booking_id=BOOKING_ID,
        category="heating",
        title="Investigate heating failure",
        case_id=case_id,
    )

    escalation_result = create_escalation_if_missing(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        reason="Human intervention required.",
        priority="high",
        case_id=case_id,
    )

    complete_task(
        task_result["task"]["task_id"]
    )

    resolve_escalation(
        escalation_result["escalation"]["escalation_id"]
    )

    result = resolve_case_if_ready(case_id)

    assert result["resolved"] is True
    assert result["reason"] == "case_resolved"

    case = result["case"]

    assert case["status"] == "resolved"
    assert case["resolved_at"] is not None


def test_case_cannot_resolve_without_operational_evidence(test_db):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating is broken.",
    )

    case_id = case_result["case"]["case_id"]

    result = resolve_case_if_ready(case_id)

    assert result["resolved"] is False
    assert result["reason"] == "no_resolution_evidence"

    case = get_case(case_id)

    assert case is not None
    assert case["status"] != "resolved"