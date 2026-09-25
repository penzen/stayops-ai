import sqlite3

from backend.services.cases import (
    ensure_case,
    get_case,
)
from backend.services.demo import reset_demo_state

from backend.services.compensation import (
    ensure_compensation_request,
    record_compensation_decision,
)


PROPERTY_ID = "prop_15"
BOOKING_ID = "book_demo_current_001"


def test_reset_demo_state_removes_cases_and_financial_state(
    test_db,
):
    # Create the operational Case.
    heating_case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating is broken.",
    )

    heating_case_id = (
        heating_case_result["case"]["case_id"]
    )

    # Create a refund Case.
    refund_case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="refund",
        summary="Guest requested compensation.",
    )

    refund_case_id = (
        refund_case_result["case"]["case_id"]
    )

    # Create a compensation request owned by the refund Case
    # and linked to the heating Case.
    compensation_result = ensure_compensation_request(
        case_id=refund_case_id,
        related_case_id=heating_case_id,
        reason="Heating disruption.",
        requested_outcome="Refund requested.",
    )

    compensation_request = (
        compensation_result["compensation_request"]
    )

    record_compensation_decision(
        compensation_request_id=(
            compensation_request[
                "compensation_request_id"
            ]
        ),
        decision="approved",
        decided_by="ops_manager_001",
        amount=100.00,
        currency="EUR",
        reason="Approved after operational review.",
    )

    assert compensation_result["created"] is True

    assert get_case(heating_case_id) is not None
    assert get_case(refund_case_id) is not None

    # Reset all mutable demo state.
    reset_result = reset_demo_state(
        BOOKING_ID
    )

    # Both Cases should have been removed.
    assert reset_result["deleted"]["cases"] == 2

    # The financial request should also have been removed.
    assert (
        reset_result["deleted"]["compensation_decisions"]
        == 1
    )
    assert (
        reset_result["deleted"]["compensation_requests"]
        == 1
    )

    assert get_case(heating_case_id) is None
    assert get_case(refund_case_id) is None

    # Verify directly that no compensation request remains.
    connection = sqlite3.connect(test_db)

    try:
        request_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM compensation_requests
            WHERE booking_id = ?
            """,
            (BOOKING_ID,),
        ).fetchone()[0]

        decision_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM compensation_decisions
            """
        ).fetchone()[0]

        assert request_count == 0
        assert decision_count == 0

    finally:
        connection.close()