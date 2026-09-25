from backend.services.cases import ensure_case

from backend.services.tasks import (
    create_task_if_missing,
)

from backend.services.escalations import (
    create_escalation_if_missing,
)

from backend.services.compensation import (
    ensure_compensation_request,
    record_compensation_decision,
    get_compensation_evidence,
)


BOOKING_ID = "book_demo_current_001"
PROPERTY_ID = "prop_15"


def create_financial_scenario():
    heating_case = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating unavailable during stay.",
    )

    heating_case_id = (
        heating_case["case"]["case_id"]
    )

    create_task_if_missing(
        property_id=PROPERTY_ID,
        booking_id=BOOKING_ID,
        category="heating",
        title="Restore guest heating.",
        case_id=heating_case_id,
    )

    create_escalation_if_missing(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        reason="Heating unavailable.",
        priority="high",
        case_id=heating_case_id,
    )

    refund_case = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="refund",
        summary="Guest requested compensation.",
    )

    compensation_result = ensure_compensation_request(
        case_id=refund_case["case"]["case_id"],
        related_case_id=heating_case_id,
        reason="Heating unavailable during stay.",
        requested_outcome="Full refund requested.",
    )

    return compensation_result[
        "compensation_request"
    ]


def test_compensation_evidence_contains_operational_context(
    test_db,
):
    request = create_financial_scenario()

    evidence = get_compensation_evidence(
        request["compensation_request_id"]
    )

    assert (
        evidence["compensation_request"][
            "compensation_request_id"
        ]
        == request["compensation_request_id"]
    )

    assert evidence["refund_case"]["category"] == "refund"

    assert (
        evidence["related_case"]["category"]
        == "heating"
    )

    assert evidence["booking"]["booking_id"] == BOOKING_ID

    operational = evidence["operational_evidence"]

    assert operational["task_count"] == 1
    assert operational["escalation_count"] == 1

    assert operational["open_task_count"] == 1
    assert operational["open_escalation_count"] == 1

    assert len(operational["tasks"]) == 1
    assert len(operational["escalations"]) == 1

    assert evidence["decision"] is None


def test_compensation_evidence_handles_no_related_case(
    test_db,
):
    refund_case = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="refund",
        summary="Guest requested compensation.",
    )

    result = ensure_compensation_request(
        case_id=refund_case["case"]["case_id"],
        reason="Guest requested compensation.",
        requested_outcome="Refund requested.",
    )

    request = result["compensation_request"]

    evidence = get_compensation_evidence(
        request["compensation_request_id"]
    )

    assert evidence["related_case"] is None

    operational = evidence["operational_evidence"]

    assert operational["task_count"] == 0
    assert operational["escalation_count"] == 0
    assert operational["tasks"] == []
    assert operational["escalations"] == []


def test_compensation_evidence_includes_human_decision(
    test_db,
):
    request = create_financial_scenario()

    record_compensation_decision(
        compensation_request_id=(
            request["compensation_request_id"]
        ),
        decision="approved",
        decided_by="ops_manager_001",
        amount=125.00,
        currency="EUR",
        reason="Extended heating disruption.",
    )

    evidence = get_compensation_evidence(
        request["compensation_request_id"]
    )

    decision = evidence["decision"]

    assert decision is not None
    assert decision["decision"] == "approved"
    assert decision["amount"] == 125.00
    assert decision["currency"] == "EUR"
    assert decision["decided_by"] == "ops_manager_001"