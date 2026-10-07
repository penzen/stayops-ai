from fastapi.testclient import TestClient

from backend.api.main import app
from backend.services.cases import (
    ensure_case,
    transition_case_status,
)
from backend.services.compensation import (
    ensure_compensation_request,
)
from backend.services.demo_sessions import (
    create_demo_session,
    get_demo_session_overview,
)
from backend.services.escalations import (
    create_escalation,
)
from backend.services.tasks import (
    create_task,
)


client = TestClient(app)


def _headers(session):
    return {
        "X-StayOps-Demo-Token":
            session["session_token"],
    }


def _stay(session, index=0):
    return session["sample_stays"][index]


def test_demo_overview_starts_with_session_stays(
    test_db,
):
    session = create_demo_session()

    overview = get_demo_session_overview(
        session["session_id"]
    )

    assert (
        overview["metrics"]["active_stays"]
        == 3
    )
    assert (
        overview["metrics"]["active_cases"]
        == 0
    )
    assert (
        overview["metrics"]["open_tasks"]
        == 0
    )
    assert len(overview["stays"]) == 3


def test_demo_overview_counts_operational_state(
    test_db,
):
    session = create_demo_session()
    stay = _stay(session)

    operational_case = ensure_case(
        booking_id=stay["booking_id"],
        property_id=stay["property_id"],
        category="heating",
        summary="Heating is unavailable.",
    )["case"]

    transition_case_status(
        case_id=operational_case["case_id"],
        new_status="waiting_human",
    )

    create_task(
        property_id=stay["property_id"],
        booking_id=stay["booking_id"],
        category="heating",
        title="Restore heating.",
        case_id=operational_case["case_id"],
    )

    create_escalation(
        booking_id=stay["booking_id"],
        property_id=stay["property_id"],
        category="heating",
        reason="Heating requires human attention.",
        priority="high",
        case_id=operational_case["case_id"],
    )

    refund_case = ensure_case(
        booking_id=stay["booking_id"],
        property_id=stay["property_id"],
        category="refund",
        summary="Guest requested compensation.",
    )["case"]

    ensure_compensation_request(
        case_id=refund_case["case_id"],
        reason="Service disruption.",
        requested_outcome="refund",
        related_case_id=operational_case["case_id"],
    )

    overview = get_demo_session_overview(
        session["session_id"]
    )

    metrics = overview["metrics"]

    assert metrics["active_cases"] == 2
    assert metrics["waiting_human"] == 1
    assert metrics["open_tasks"] == 1
    assert metrics["open_escalations"] == 1
    assert (
        metrics["pending_financial_reviews"]
        == 1
    )

    heating = next(
        item
        for item in overview["attention"]
        if item["category"] == "heating"
    )

    assert heating["priority"] == "high"
    assert heating["open_task_count"] == 1
    assert heating["open_escalation_count"] == 1


def test_demo_overview_is_session_scoped(
    test_db,
):
    first = create_demo_session()
    second = create_demo_session()

    first_stay = _stay(first)
    second_stay = _stay(second)

    first_case = ensure_case(
        booking_id=first_stay["booking_id"],
        property_id=first_stay["property_id"],
        category="heating",
        summary="First session.",
    )["case"]

    second_case = ensure_case(
        booking_id=second_stay["booking_id"],
        property_id=second_stay["property_id"],
        category="plumbing",
        summary="Second session.",
    )["case"]

    overview = get_demo_session_overview(
        first["session_id"]
    )

    case_ids = {
        item["case_id"]
        for item in overview["attention"]
    }

    assert first_case["case_id"] in case_ids
    assert second_case["case_id"] not in case_ids
    assert (
        overview["metrics"]["active_cases"]
        == 1
    )


def test_demo_overview_api_is_session_scoped(
    test_db,
):
    session = create_demo_session()

    response = client.get(
        "/demo/sessions/overview",
        headers=_headers(session),
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["session"]["session_id"]
        == session["session_id"]
    )
    assert (
        data["metrics"]["active_stays"]
        == 3
    )
