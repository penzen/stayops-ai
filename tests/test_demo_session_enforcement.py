from fastapi.testclient import TestClient

from backend.api.main import app
from backend.services.cases import (
    ensure_case,
    transition_case_status,
)
from backend.services.demo_sessions import (
    create_demo_session,
)
from backend.services.incidents import (
    create_incident,
    get_open_incidents,
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


def _first_stay(session):
    return session["sample_stays"][0]


def test_session_cannot_read_another_sessions_messages(
    test_db,
):
    first = create_demo_session()
    second = create_demo_session()

    second_booking = (
        _first_stay(second)["booking_id"]
    )

    response = client.get(
        f"/reservations/{second_booking}/messages",
        headers=_headers(first),
    )

    assert response.status_code == 403


def test_operations_queue_is_scoped_to_session(
    test_db,
):
    first = create_demo_session()
    second = create_demo_session()

    first_stay = _first_stay(first)
    second_stay = _first_stay(second)

    first_case = ensure_case(
        booking_id=first_stay["booking_id"],
        property_id=first_stay["property_id"],
        category="heating",
        summary="First session heating issue.",
    )["case"]

    second_case = ensure_case(
        booking_id=second_stay["booking_id"],
        property_id=second_stay["property_id"],
        category="heating",
        summary="Second session heating issue.",
    )["case"]

    transition_case_status(
        case_id=first_case["case_id"],
        new_status="waiting_human",
    )
    transition_case_status(
        case_id=second_case["case_id"],
        new_status="waiting_human",
    )

    response = client.get(
        "/operations/queue",
        headers=_headers(first),
    )

    assert response.status_code == 200

    case_ids = {
        entry["case"]["case_id"]
        for entry in response.json()
    }

    assert first_case["case_id"] in case_ids
    assert second_case["case_id"] not in case_ids


def test_property_tasks_are_scoped_to_session(
    test_db,
):
    first = create_demo_session()
    second = create_demo_session()

    first_stay = _first_stay(first)
    second_stay = _first_stay(second)

    first_task = create_task(
        property_id=first_stay["property_id"],
        booking_id=first_stay["booking_id"],
        category="heating",
        title="First session task.",
    )

    second_task = create_task(
        property_id=second_stay["property_id"],
        booking_id=second_stay["booking_id"],
        category="heating",
        title="Second session task.",
    )

    response = client.get(
        f"/properties/{first_stay['property_id']}/tasks",
        headers=_headers(first),
    )

    assert response.status_code == 200

    task_ids = {
        task["task_id"]
        for task in response.json()
    }

    assert first_task["task_id"] in task_ids
    assert second_task["task_id"] not in task_ids


def test_cross_session_agent_request_is_blocked_before_model(
    test_db,
):
    first = create_demo_session()
    second = create_demo_session()
    second_stay = _first_stay(second)

    response = client.post(
        "/agent/chat",
        headers=_headers(first),
        json={
            "guest_id": second_stay["guest_id"],
            "booking_id": second_stay["booking_id"],
            "message": "The heating is broken.",
        },
    )

    assert response.status_code == 403


def test_cross_session_reset_is_blocked(
    test_db,
):
    first = create_demo_session()
    second = create_demo_session()
    second_booking = _first_stay(second)["booking_id"]

    response = client.post(
        f"/demo/reset/{second_booking}",
        headers=_headers(first),
    )

    assert response.status_code == 403


def test_session_sample_stay_can_be_reset(
    test_db,
):
    session = create_demo_session()
    booking_id = _first_stay(session)["booking_id"]

    response = client.post(
        f"/demo/reset/{booking_id}",
        headers=_headers(session),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "reset"


def test_incident_lookup_can_be_booking_scoped(
    test_db,
):
    first = create_demo_session()
    second = create_demo_session()
    first_stay = _first_stay(first)
    second_stay = _first_stay(second)

    first_incident = create_incident(
        property_id=first_stay["property_id"],
        booking_id=first_stay["booking_id"],
        category="heating",
        description="First session incident.",
    )

    second_incident = create_incident(
        property_id=second_stay["property_id"],
        booking_id=second_stay["booking_id"],
        category="heating",
        description="Second session incident.",
    )

    incidents = get_open_incidents(
        first_stay["property_id"],
        booking_id=first_stay["booking_id"],
    )

    incident_ids = {
        incident["incident_id"]
        for incident in incidents
    }

    assert first_incident["incident_id"] in incident_ids
    assert second_incident["incident_id"] not in incident_ids


def test_protected_endpoint_requires_token_without_legacy_mode(
    test_db,
    monkeypatch,
):
    monkeypatch.delenv(
        "STAYOPS_ALLOW_LEGACY_DEMO",
        raising=False,
    )

    response = client.get(
        "/operations/queue"
    )

    assert response.status_code == 401
