import pytest

from backend.services.cases import (
    ensure_case,
    get_case,
    transition_case_status,
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

    resolved = transition_case_status(
        case_id=case_id,
        new_status="resolved",
    )

    assert resolved["transitioned"] is True
    assert resolved["from_status"] == "in_progress"
    assert resolved["to_status"] == "resolved"
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

    transition_case_status(
        case_id=case_id,
        new_status="resolved",
    )

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