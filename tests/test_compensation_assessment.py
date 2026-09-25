from backend.services.cases import ensure_case

from backend.services.tasks import (
    create_task_if_missing,
)

from backend.services.escalations import (
    create_escalation_if_missing,
)

from backend.services.compensation import (
    ensure_compensation_request,
    build_compensation_assessment,
)


BOOKING_ID = "book_demo_current_001"
PROPERTY_ID = "prop_15"


def create_compensation_scenario(
    *,
    category="heating",
    priority="high",
):
    operational_case = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category=category,
        summary="Operational disruption during stay.",
    )

    operational_case_id = (
        operational_case["case"]["case_id"]
    )

    create_task_if_missing(
        property_id=PROPERTY_ID,
        booking_id=BOOKING_ID,
        category=category,
        title="Resolve operational issue.",
        case_id=operational_case_id,
    )

    create_escalation_if_missing(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category=category,
        reason="Guest experience affected.",
        priority=priority,
        case_id=operational_case_id,
    )

    refund_case = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="refund",
        summary="Guest requested compensation.",
    )

    request_result = ensure_compensation_request(
        case_id=refund_case["case"]["case_id"],
        related_case_id=operational_case_id,
        reason="Operational disruption.",
        requested_outcome="Refund requested.",
    )

    return request_result[
        "compensation_request"
    ]


def test_assessment_identifies_high_severity_operational_issue(
    test_db,
):
    request = create_compensation_scenario(
        category="heating",
        priority="high",
    )

    assessment = build_compensation_assessment(
        request["compensation_request_id"]
    )

    assert assessment["severity"] == "high"

    assert (
        assessment["human_review_required"]
        is True
    )

    assert (
        "high_priority_escalation"
        in assessment["factors"]
    )


def test_assessment_detects_open_operational_work(
    test_db,
):
    request = create_compensation_scenario()

    assessment = build_compensation_assessment(
        request["compensation_request_id"]
    )

    assert assessment["operational_work_open"] is True

    assert (
        "unresolved_operational_work"
        in assessment["factors"]
    )


def test_assessment_without_operational_case_is_limited(
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

    assessment = build_compensation_assessment(
        request["compensation_request_id"]
    )

    assert assessment["severity"] == "unknown"

    assert (
        assessment["operational_evidence_available"]
        is False
    )

    assert (
        "missing_operational_evidence"
        in assessment["factors"]
    )


def test_assessment_never_approves_compensation(
    test_db,
):
    request = create_compensation_scenario()

    assessment = build_compensation_assessment(
        request["compensation_request_id"]
    )

    assert "approved" not in assessment
    assert "amount" not in assessment
    assert "currency" not in assessment

    assert (
        assessment["human_review_required"]
        is True
    )