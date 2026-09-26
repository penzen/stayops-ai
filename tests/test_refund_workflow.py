from backend.services.compensation import (
    ensure_refund_workflow,
    record_compensation_decision,
)
from backend.services.cases import (
    resolve_case_if_ready,
)
from backend.services.escalations import (
    resolve_escalation,
)
from backend.services.db import get_connection


PROPERTY_ID = "prop_15"
BOOKING_ID = "book_demo_current_001"


def test_refund_workflow_creates_complete_financial_state(
    test_db,
):
    result = ensure_refund_workflow(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        reason="Heating failed during the stay.",
        requested_outcome="Full refund",
        explicit_new_request=True,
    )

    assert result["historical"] is False

    refund_case = result["case"]
    request = result["compensation_request"]
    escalation = result["escalation"]

    assert refund_case["category"] == "refund"
    assert refund_case["status"] == "waiting_human"

    assert request["case_id"] == refund_case["case_id"]
    assert request["status"] == "pending_review"

    assert escalation["case_id"] == refund_case["case_id"]
    assert escalation["category"] == "refund"
    assert escalation["status"] == "open"


def test_refund_workflow_reuses_active_workflow(
    test_db,
):
    first = ensure_refund_workflow(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        reason="Heating failed during the stay.",
        requested_outcome="Full refund",
        explicit_new_request=True,
    )

    second = ensure_refund_workflow(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        reason="Guest asks about the existing refund.",
        requested_outcome="Full refund",
        explicit_new_request=False,
    )

    assert second["historical"] is False

    assert (
        second["case"]["case_id"]
        == first["case"]["case_id"]
    )

    assert (
        second["compensation_request"][
            "compensation_request_id"
        ]
        == first["compensation_request"][
            "compensation_request_id"
        ]
    )

    assert (
        second["escalation"]["escalation_id"]
        == first["escalation"]["escalation_id"]
    )

    assert second["case_created"] is False
    assert second["compensation_request_created"] is False
    assert second["escalation_created"] is False


def test_refund_workflow_returns_resolved_history_without_duplicates(
    test_db,
):
    first = ensure_refund_workflow(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        reason="Heating failed during the stay.",
        requested_outcome="Full refund",
        explicit_new_request=True,
    )

    case_id = first["case"]["case_id"]

    compensation_request_id = (
        first["compensation_request"][
            "compensation_request_id"
        ]
    )

    escalation_id = (
        first["escalation"][
            "escalation_id"
        ]
    )

    record_compensation_decision(
        compensation_request_id=compensation_request_id,
        decision="approved",
        decided_by="GRO_254",
        reason="Confirmed service disruption.",
        amount=150.0,
        currency="EUR",
    )

    resolve_escalation(
        escalation_id
    )

    resolution = resolve_case_if_ready(
        case_id
    )

    assert resolution["resolved"] is True

    historical = ensure_refund_workflow(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        reason="Can you confirm whether my refund is complete?",
        explicit_new_request=False,
    )

    assert historical["historical"] is True
    assert historical["created"] is False

    assert (
        historical["case"]["case_id"]
        == case_id
    )

    connection = get_connection()

    try:
        refund_cases = connection.execute(
            """
            SELECT *
            FROM cases
            WHERE booking_id = ?
              AND category = 'refund'
            """,
            (BOOKING_ID,),
        ).fetchall()

        requests = connection.execute(
            """
            SELECT *
            FROM compensation_requests
            WHERE booking_id = ?
            """,
            (BOOKING_ID,),
        ).fetchall()

        escalations = connection.execute(
            """
            SELECT *
            FROM escalations
            WHERE booking_id = ?
              AND category = 'refund'
            """,
            (BOOKING_ID,),
        ).fetchall()

    finally:
        connection.close()

    assert len(refund_cases) == 1
    assert len(requests) == 1
    assert len(escalations) == 1

    assert refund_cases[0]["status"] == "resolved"


def test_refund_workflow_creates_new_request_after_resolved_history(
    test_db,
):
    first = ensure_refund_workflow(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        reason="Heating failed during the stay.",
        requested_outcome="Full refund",
        explicit_new_request=True,
    )

    first_case_id = first["case"]["case_id"]
    first_request_id = (
        first["compensation_request"][
            "compensation_request_id"
        ]
    )
    first_escalation_id = (
        first["escalation"]["escalation_id"]
    )

    record_compensation_decision(
        compensation_request_id=first_request_id,
        decision="approved",
        decided_by="GRO_254",
        reason="Confirmed service disruption.",
        amount=150.0,
        currency="EUR",
    )

    resolve_escalation(
        first_escalation_id
    )

    resolution = resolve_case_if_ready(
        first_case_id
    )

    assert resolution["resolved"] is True

    second = ensure_refund_workflow(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        reason=(
            "The heating failed again during a different "
            "part of the stay and I want another refund review."
        ),
        requested_outcome="Additional refund",
        explicit_new_request=True,
    )

    assert second["historical"] is False
    assert second["created"] is True

    assert (
        second["case"]["case_id"]
        != first_case_id
    )

    assert (
        second["compensation_request"][
            "compensation_request_id"
        ]
        != first_request_id
    )

    assert (
        second["escalation"]["escalation_id"]
        != first_escalation_id
    )

    assert second["case"]["status"] == "waiting_human"
    assert (
        second["compensation_request"]["status"]
        == "pending_review"
    )
    assert second["escalation"]["status"] == "open"

    connection = get_connection()

    try:
        refund_cases = connection.execute(
            """
            SELECT *
            FROM cases
            WHERE booking_id = ?
              AND category = 'refund'
            ORDER BY created_at ASC
            """,
            (BOOKING_ID,),
        ).fetchall()

        requests = connection.execute(
            """
            SELECT *
            FROM compensation_requests
            WHERE booking_id = ?
            """,
            (BOOKING_ID,),
        ).fetchall()

        escalations = connection.execute(
            """
            SELECT *
            FROM escalations
            WHERE booking_id = ?
              AND category = 'refund'
            """,
            (BOOKING_ID,),
        ).fetchall()

    finally:
        connection.close()

    assert len(refund_cases) == 2
    assert len(requests) == 2
    assert len(escalations) == 2

    old_case = next(
        case
        for case in refund_cases
        if case["case_id"] == first_case_id
    )

    assert old_case["status"] == "resolved"