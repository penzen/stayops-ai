import pytest

from backend.services.cases import ensure_case

from backend.services.compensation import (
    ensure_compensation_request,
)


BOOKING_ID = "book_demo_current_001"
PROPERTY_ID = "prop_15"


def test_create_compensation_request_linked_to_refund_case(
    test_db,
):
    heating_case = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating failed during active stay.",
    )

    refund_case = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="refund",
        summary="Guest requested compensation.",
    )

    result = ensure_compensation_request(
        case_id=refund_case["case"]["case_id"],
        related_case_id=(
            heating_case["case"]["case_id"]
        ),
        reason=(
            "Heating was unavailable for several hours."
        ),
        requested_outcome="Full refund requested.",
    )

    assert result["created"] is True

    request = result["compensation_request"]

    assert (
        request["case_id"]
        == refund_case["case"]["case_id"]
    )

    assert (
        request["related_case_id"]
        == heating_case["case"]["case_id"]
    )

    assert request["booking_id"] == BOOKING_ID
    assert request["property_id"] == PROPERTY_ID
    assert request["status"] == "pending_review"


def test_compensation_request_is_idempotent_per_refund_case(
    test_db,
):
    refund_case = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="refund",
        summary="Guest requested compensation.",
    )

    case_id = refund_case["case"]["case_id"]

    first = ensure_compensation_request(
        case_id=case_id,
        reason="Heating disruption.",
        requested_outcome="Refund requested.",
    )

    second = ensure_compensation_request(
        case_id=case_id,
        reason="Heating disruption.",
        requested_outcome="Refund requested.",
    )

    assert first["created"] is True
    assert second["created"] is False

    assert (
        first["compensation_request"][
            "compensation_request_id"
        ]
        ==
        second["compensation_request"][
            "compensation_request_id"
        ]
    )


def test_compensation_request_requires_refund_case(
    test_db,
):
    heating_case = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating failed.",
    )

    with pytest.raises(
        ValueError,
        match="refund Case",
    ):
        ensure_compensation_request(
            case_id=heating_case["case"]["case_id"],
            reason="Heating disruption.",
            requested_outcome="Refund requested.",
        )