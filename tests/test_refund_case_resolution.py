from backend.services.escalations import (
    create_escalation_if_missing,
    resolve_escalation,
)

from backend.services.compensation import (
    ensure_compensation_request,
    record_compensation_decision,
)

from backend.services.cases import (
    ensure_case,
    transition_case_status,
    claim_case,
    resolve_case_if_ready,
)


BOOKING_ID = "book_demo_current_001"
PROPERTY_ID = "prop_15"


def create_refund_case():
    refund_case = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="refund",
        summary="Guest requested compensation.",
    )

    case_id = refund_case["case"]["case_id"]

    escalation = create_escalation_if_missing(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="refund",
        reason="Compensation requires human review.",
        priority="medium",
        case_id=case_id,
    )

    return (
        refund_case["case"],
        escalation["escalation"],
    )


def test_refund_case_cannot_resolve_without_compensation_request(
    test_db,
):
    case, escalation = create_refund_case()

    resolve_escalation(
        escalation["escalation_id"],
    )

    result = resolve_case_if_ready(
        case["case_id"]
    )

    assert result["resolved"] is False
    assert (
        result["reason"]
        == "compensation_request_missing"
    )


def test_refund_case_cannot_resolve_without_financial_decision(
    test_db,
):
    case, escalation = create_refund_case()

    ensure_compensation_request(
        case_id=case["case_id"],
        reason="Heating disruption.",
        requested_outcome="Refund requested.",
    )

    resolve_escalation(
        escalation["escalation_id"],
    )

    result = resolve_case_if_ready(
        case["case_id"]
    )

    assert result["resolved"] is False
    assert (
        result["reason"]
        == "financial_decision_pending"
    )


def test_refund_case_resolves_after_human_financial_decision(
    test_db,
):
    case, escalation = create_refund_case()

    transition_case_status(
    case_id=case["case_id"],
    new_status="waiting_human",
)

    claim_case(
        case_id=case["case_id"],
        operator_id="GRO_254",
    )

    request_result = ensure_compensation_request(
        case_id=case["case_id"],
        reason="Heating disruption.",
        requested_outcome="Refund requested.",
    )

    request = request_result[
        "compensation_request"
    ]

    record_compensation_decision(
        compensation_request_id=(
            request["compensation_request_id"]
        ),
        decision="approved",
        decided_by="GRO_254",
        amount=100.00,
        currency="EUR",
        reason="Approved after review.",
    )

    resolve_escalation(
        escalation["escalation_id"],
        operator_id="GRO_254",
    )

    result = resolve_case_if_ready(
        case["case_id"]
    )

    assert result["resolved"] is True
    assert result["reason"] == "case_resolved"
    assert result["case"]["status"] == "resolved"