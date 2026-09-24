import pytest

from backend.services.cases import (
    ensure_case,
    transition_case_status,
    resolve_case_if_ready,
    get_open_cases_for_booking,
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

def test_case_can_progress_through_lifecycle(test_db):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating is broken.",
    )

    case_id = case_result["case"]["case_id"]

    in_progress = transition_case_status(
        case_id=case_id,
        new_status="in_progress",
    )

    assert in_progress["transitioned"] is True
    assert in_progress["from_status"] == "open"
    assert in_progress["to_status"] == "in_progress"
    assert in_progress["case"]["status"] == "in_progress"
    assert in_progress["case"]["resolved_at"] is None

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

    resolved = resolve_case_if_ready(
        case_id
    )

    assert resolved["resolved"] is True
    assert resolved["reason"] == "case_resolved"
    assert resolved["case"]["status"] == "resolved"
    assert resolved["case"]["resolved_at"] is not None

def test_resolved_case_cannot_transition_again(test_db):
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

    resolution = resolve_case_if_ready(
        case_id
    )

    assert resolution["resolved"] is True

    with pytest.raises(
        ValueError,
        match="Invalid Case transition",
    ):
        transition_case_status(
            case_id=case_id,
            new_status="in_progress",
        )


def test_same_case_status_is_idempotent(test_db):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating is broken.",
    )

    case_id = case_result["case"]["case_id"]

    result = transition_case_status(
        case_id=case_id,
        new_status="open",
    )

    assert result["transitioned"] is False
    assert result["reason"] == "already_in_status"
    assert result["case"]["status"] == "open"


def test_ensure_case_reuses_waiting_human_case(test_db):
    first_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating is broken.",
    )

    case_id = first_result["case"]["case_id"]

    transition_case_status(
        case_id=case_id,
        new_status="waiting_human",
    )

    second_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating is still broken.",
    )

    assert second_result["created"] is False
    assert second_result["case"]["case_id"] == case_id
    assert second_result["case"]["status"] == "waiting_human"

def test_waiting_human_case_is_still_returned_as_active(test_db):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating is broken.",
    )

    case_id = case_result["case"]["case_id"]

    transition_case_status(
        case_id=case_id,
        new_status="waiting_human",
    )

    cases = get_open_cases_for_booking(
        BOOKING_ID
    )

    case_ids = {
        case["case_id"]
        for case in cases
    }

    assert case_id in case_ids


def test_generic_transition_cannot_resolve_case(test_db):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating is broken.",
    )

    case_id = case_result["case"]["case_id"]

    transition_case_status(
        case_id=case_id,
        new_status="waiting_human",
    )

    with pytest.raises(
        ValueError,
        match="Invalid Case transition",
    ):
        transition_case_status(
            case_id=case_id,
            new_status="resolved",
        )