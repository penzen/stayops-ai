from fastapi.testclient import TestClient

from backend.api.main import app
from backend.services.cases import (
    ensure_case,
    transition_case_status,
)
from backend.services.demo_guests import (
    create_demo_guest_stay,
)
from backend.services.demo_sessions import (
    create_demo_session,
    get_demo_session_guest_detail,
    get_demo_session_guests,
)
from backend.services.escalations import (
    create_escalation,
)
from backend.services.messages import (
    send_message,
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


def test_guest_directory_returns_session_guests(
    test_db,
):
    session = create_demo_session()

    guests = get_demo_session_guests(
        session["session_id"]
    )

    assert len(guests) == 3
    assert {
        guest["guest_id"]
        for guest in guests
    } == {
        stay["guest_id"]
        for stay in session["sample_stays"]
    }


def test_guest_directory_reflects_operational_state(
    test_db,
):
    session = create_demo_session()
    stay = _stay(session)

    case = ensure_case(
        booking_id=stay["booking_id"],
        property_id=stay["property_id"],
        category="heating",
        summary="Heating stopped working.",
    )["case"]

    transition_case_status(
        case_id=case["case_id"],
        new_status="waiting_human",
    )

    create_task(
        property_id=stay["property_id"],
        booking_id=stay["booking_id"],
        category="heating",
        title="Restore heating.",
        case_id=case["case_id"],
    )

    create_escalation(
        booking_id=stay["booking_id"],
        property_id=stay["property_id"],
        category="heating",
        reason="Heating requires operator attention.",
        priority="high",
        case_id=case["case_id"],
    )

    send_message(
        booking_id=stay["booking_id"],
        guest_id=stay["guest_id"],
        sender_type="guest",
        message_text="The apartment is cold.",
    )

    guests = get_demo_session_guests(
        session["session_id"]
    )

    item = next(
        guest
        for guest in guests
        if (
            guest["guest_id"]
            == stay["guest_id"]
        )
    )

    assert (
        item["operational_status"]
        == "needs_human"
    )
    assert item["active_case_count"] == 1
    assert item["waiting_human_count"] == 1
    assert item["open_task_count"] == 1
    assert item["open_escalation_count"] == 1
    assert item["message_count"] == 1


def test_guest_directory_is_session_scoped(
    test_db,
):
    first = create_demo_session()
    second = create_demo_session()

    first_ids = {
        guest["guest_id"]
        for guest in get_demo_session_guests(
            first["session_id"]
        )
    }

    second_ids = {
        guest["guest_id"]
        for guest in get_demo_session_guests(
            second["session_id"]
        )
    }

    assert first_ids.isdisjoint(
        second_ids
    )


def test_guest_detail_returns_operational_context(
    test_db,
):
    session = create_demo_session()
    stay = _stay(session)

    case = ensure_case(
        booking_id=stay["booking_id"],
        property_id=stay["property_id"],
        category="plumbing",
        summary="Sink is leaking.",
    )["case"]

    create_task(
        property_id=stay["property_id"],
        booking_id=stay["booking_id"],
        category="plumbing",
        title="Inspect sink leak.",
        case_id=case["case_id"],
    )

    send_message(
        booking_id=stay["booking_id"],
        guest_id=stay["guest_id"],
        sender_type="guest",
        message_text="The sink is leaking.",
    )

    detail = get_demo_session_guest_detail(
        session_id=session["session_id"],
        guest_id=stay["guest_id"],
    )

    assert (
        detail["guest"]["guest_id"]
        == stay["guest_id"]
    )
    assert (
        detail["reservation"]["booking_id"]
        == stay["booking_id"]
    )
    assert len(detail["cases"]) == 1
    assert len(detail["tasks"]) == 1
    assert len(detail["messages"]) == 1
    assert (
        detail["operational_status"]
        == "active_issue"
    )


def test_guest_detail_api_blocks_cross_session_access(
    test_db,
):
    first = create_demo_session()
    second = create_demo_session()

    target_guest_id = (
        _stay(second)["guest_id"]
    )

    response = client.get(
        (
            "/demo/sessions/guests/"
            f"{target_guest_id}"
        ),
        headers=_headers(first),
    )

    assert response.status_code == 403


def test_custom_guest_appears_in_directory(
    test_db,
):
    session = create_demo_session()

    created = create_demo_guest_stay(
        first_name="Maya",
        last_name="Patel",
        guest_lang="en",
        property_id="prop_15",
        session_id=session["session_id"],
    )

    guests = get_demo_session_guests(
        session["session_id"]
    )

    custom = next(
        item
        for item in guests
        if (
            item["guest_id"]
            == created["guest_id"]
        )
    )

    assert (
        custom["resource_kind"]
        == "custom"
    )
    assert (
        custom["operational_status"]
        == "clear"
    )
