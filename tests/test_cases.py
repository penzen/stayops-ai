from backend.services.tasks import create_task_if_missing
from backend.services.escalations import create_escalation_if_missing
from backend.services.cases import (
    ensure_case,
    get_case,
    get_open_cases_for_booking,
)

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

def test_same_issue_reuses_case_task_and_escalation(test_db):
    first_case = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="plumbing",
        summary="Guest reported a leaking kitchen sink.",
    )

    first_case_id = first_case["case"]["case_id"]

    first_task = create_task_if_missing(
        property_id=PROPERTY_ID,
        booking_id=BOOKING_ID,
        category="plumbing",
        title="Investigate kitchen sink leak",
        case_id=first_case_id,
    )

    first_escalation = create_escalation_if_missing(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="plumbing",
        reason="Leak requires human coordination.",
        priority="high",
        case_id=first_case_id,
    )

    second_case = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="plumbing",
        summary="Guest reports the sink is still leaking.",
    )

    second_case_id = second_case["case"]["case_id"]

    second_task = create_task_if_missing(
        property_id=PROPERTY_ID,
        booking_id=BOOKING_ID,
        category="plumbing",
        title="Investigate recurring kitchen sink leak",
        case_id=second_case_id,
    )

    second_escalation = create_escalation_if_missing(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="plumbing",
        reason="Guest reports the same leak again.",
        priority="high",
        case_id=second_case_id,
    )

    assert first_case["created"] is True
    assert second_case["created"] is False

    assert first_case_id == second_case_id

    assert first_task["created"] is True
    assert second_task["created"] is False

    assert (
        first_task["task"]["task_id"]
        == second_task["task"]["task_id"]
    )

    assert first_escalation["created"] is True
    assert second_escalation["created"] is False

    assert (
        first_escalation["escalation"]["escalation_id"]
        == second_escalation["escalation"]["escalation_id"]
    )

    assert first_task["task"]["case_id"] == first_case_id

    assert (
        first_escalation["escalation"]["case_id"]
        == first_case_id
    )

def test_get_case_returns_created_case(test_db):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="plumbing",
        summary="Guest reported a leaking kitchen sink.",
    )

    case_id = case_result["case"]["case_id"]

    case = get_case(case_id)

    assert case is not None
    assert case["case_id"] == case_id
    assert case["booking_id"] == BOOKING_ID
    assert case["property_id"] == PROPERTY_ID
    assert case["category"] == "plumbing"
    assert case["status"] == "open"

def test_get_open_cases_for_booking(test_db):
    plumbing_case = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="plumbing",
        summary="Guest reported a leaking kitchen sink.",
    )

    heating_case = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Guest reported that heating is not working.",
    )

    cases = get_open_cases_for_booking(BOOKING_ID)

    case_ids = {
        case["case_id"]
        for case in cases
    }

    assert plumbing_case["case"]["case_id"] in case_ids
    assert heating_case["case"]["case_id"] in case_ids


def test_case_adopts_existing_unlinked_task(test_db):
    legacy_task = create_task_if_missing(
        property_id=PROPERTY_ID,
        booking_id=BOOKING_ID,
        category="plumbing",
        title="Investigate kitchen sink leak",
    )

    assert legacy_task["task"]["case_id"] is None

    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="plumbing",
        summary="Guest reported a leaking kitchen sink.",
    )

    case_id = case_result["case"]["case_id"]

    adopted_task = create_task_if_missing(
        property_id=PROPERTY_ID,
        booking_id=BOOKING_ID,
        category="plumbing",
        title="Investigate kitchen sink leak",
        case_id=case_id,
    )

    assert adopted_task["created"] is False

    assert (
        adopted_task["task"]["task_id"]
        == legacy_task["task"]["task_id"]
    )

    assert adopted_task["task"]["case_id"] == case_id


def test_case_adopts_existing_unlinked_escalation(test_db):
    legacy_escalation = create_escalation_if_missing(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="plumbing",
        reason="Leak requires human coordination.",
        priority="high",
    )

    assert legacy_escalation["escalation"]["case_id"] is None

    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="plumbing",
        summary="Guest reported a leaking kitchen sink.",
    )

    case_id = case_result["case"]["case_id"]

    adopted_escalation = create_escalation_if_missing(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="plumbing",
        reason="Leak still requires human coordination.",
        priority="high",
        case_id=case_id,
    )

    assert adopted_escalation["created"] is False

    assert (
        adopted_escalation["escalation"]["escalation_id"]
        == legacy_escalation["escalation"]["escalation_id"]
    )

    assert (
        adopted_escalation["escalation"]["case_id"]
        == case_id
    )

"""
FIRST REPORT

plumbing issue
      ↓
Case A
 ├── Task A
 └── Escalation A


SECOND REPORT

same plumbing issue
      ↓
Case A
 ├── Task A
 └── Escalation A

NO DUPLICATES

"""