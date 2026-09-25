import pytest

from backend.services.cases import ensure_case
from backend.services.compensation import (
    ensure_compensation_request,
    record_compensation_decision,
)


BOOKING_ID = "book_demo_current_001"
PROPERTY_ID = "prop_15"


def create_pending_request():
    refund_case = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="refund",
        summary="Guest requested compensation.",
    )

    request_result = ensure_compensation_request(
        case_id=refund_case["case"]["case_id"],
        reason="Heating disruption.",
        requested_outcome="Refund requested.",
    )

    return request_result["compensation_request"]


def test_human_can_approve_compensation_request(
    test_db,
):
    request = create_pending_request()

    result = record_compensation_decision(
        compensation_request_id=(
            request["compensation_request_id"]
        ),
        decision="approved",
        decided_by="ops_manager_001",
        amount=150.00,
        currency="EUR",
        reason="Heating unavailable for extended period.",
    )

    assert result["created"] is True

    decision = result["decision"]

    assert decision["decision"] == "approved"
    assert decision["amount"] == 150.00
    assert decision["currency"] == "EUR"
    assert decision["decided_by"] == "ops_manager_001"


def test_human_can_deny_compensation_request(
    test_db,
):
    request = create_pending_request()

    result = record_compensation_decision(
        compensation_request_id=(
            request["compensation_request_id"]
        ),
        decision="denied",
        decided_by="ops_manager_001",
        reason="Request does not meet compensation policy.",
    )

    assert result["created"] is True

    decision = result["decision"]

    assert decision["decision"] == "denied"
    assert decision["amount"] is None


def test_approved_decision_requires_amount(
    test_db,
):
    request = create_pending_request()

    with pytest.raises(
        ValueError,
        match="amount",
    ):
        record_compensation_decision(
            compensation_request_id=(
                request["compensation_request_id"]
            ),
            decision="approved",
            decided_by="ops_manager_001",
            reason="Approved by operations.",
        )


def test_denied_decision_cannot_have_amount(
    test_db,
):
    request = create_pending_request()

    with pytest.raises(
        ValueError,
        match="amount",
    ):
        record_compensation_decision(
            compensation_request_id=(
                request["compensation_request_id"]
            ),
            decision="denied",
            decided_by="ops_manager_001",
            amount=100.00,
            currency="EUR",
            reason="Denied.",
        )


def test_compensation_decision_is_final(
    test_db,
):
    request = create_pending_request()

    request_id = request[
        "compensation_request_id"
    ]

    first = record_compensation_decision(
        compensation_request_id=request_id,
        decision="approved",
        decided_by="ops_manager_001",
        amount=100.00,
        currency="EUR",
        reason="Approved.",
    )

    second = record_compensation_decision(
        compensation_request_id=request_id,
        decision="approved",
        decided_by="ops_manager_001",
        amount=100.00,
        currency="EUR",
        reason="Approved.",
    )

    assert first["created"] is True
    assert second["created"] is False

    assert (
        first["decision"]["compensation_decision_id"]
        ==
        second["decision"]["compensation_decision_id"]
    )


def test_invalid_compensation_decision_is_rejected(
    test_db,
):
    request = create_pending_request()

    with pytest.raises(
        ValueError,
        match="decision",
    ):
        record_compensation_decision(
            compensation_request_id=(
                request["compensation_request_id"]
            ),
            decision="maybe",
            decided_by="ops_manager_001",
            reason="Invalid decision.",
        )