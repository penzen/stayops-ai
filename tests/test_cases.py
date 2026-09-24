from backend.services.cases import ensure_case
from backend.services.tasks import create_task_if_missing
from backend.services.escalations import create_escalation_if_missing

PROPERTY_ID = "prop_15"
BOOKING_ID = "book_demo_current_001"


def test_ensure_case_reuses_existing_open_case(test_db):
    first_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="plumbing",
        summary="Guest reported a leaking kitchen sink.",
    )

    second_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="plumbing",
        summary="Guest reports the sink is still leaking.",
    )

    assert first_result["created"] is True
    assert first_result["reason"] == "case_created"

    assert second_result["created"] is False
    assert second_result["reason"] == "existing_open_case"

    assert (
        first_result["case"]["case_id"]
        == second_result["case"]["case_id"]
    )

def test_case_can_own_idempotent_task(test_db):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="plumbing",
        summary="Guest reported a leaking kitchen sink.",
    )

    case_id = case_result["case"]["case_id"]

    first_task = create_task_if_missing(
        property_id=PROPERTY_ID,
        booking_id=BOOKING_ID,
        category="plumbing",
        title="Investigate kitchen sink leak",
        case_id=case_id,
    )

    second_task = create_task_if_missing(
        property_id=PROPERTY_ID,
        booking_id=BOOKING_ID,
        category="plumbing",
        title="Investigate kitchen sink leak again",
        case_id=case_id,
    )

    assert first_task["created"] is True
    assert second_task["created"] is False

    assert (
        first_task["task"]["task_id"]
        == second_task["task"]["task_id"]
    )

    assert first_task["task"]["case_id"] == case_id
    assert second_task["task"]["case_id"] == case_id

def test_case_can_own_idempotent_escalation(test_db):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="plumbing",
        summary="Guest reported a leaking kitchen sink.",
    )

    case_id = case_result["case"]["case_id"]

    first_escalation = create_escalation_if_missing(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="plumbing",
        reason="Leak requires human coordination.",
        priority="high",
        case_id=case_id,
    )

    second_escalation = create_escalation_if_missing(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="plumbing",
        reason="Second attempt for same plumbing issue.",
        priority="high",
        case_id=case_id,
    )

    assert first_escalation["created"] is True
    assert second_escalation["created"] is False

    assert (
        first_escalation["escalation"]["escalation_id"]
        == second_escalation["escalation"]["escalation_id"]
    )

    assert (
        first_escalation["escalation"]["case_id"]
        == case_id
    )

    assert (
        second_escalation["escalation"]["case_id"]
        == case_id
    )