from fastapi.testclient import TestClient

from backend.api.main import app
from backend.services.cases import (
    ensure_case,
)
from backend.services.demo_sessions import (
    create_demo_session,
    search_demo_session,
)


client = TestClient(app)


def _headers(session):
    return {
        "X-StayOps-Demo-Token":
            session["session_token"],
    }


def _stay(session, index=0):
    return session["sample_stays"][index]


def test_search_finds_guest_by_name(
    test_db,
):
    session = create_demo_session()

    result = search_demo_session(
        session_id=session["session_id"],
        query="Emma",
    )

    assert any(
        item["first_name"] == "Emma"
        for item in result["guests"]
    )


def test_search_finds_booking_by_id(
    test_db,
):
    session = create_demo_session()
    stay = _stay(session)

    result = search_demo_session(
        session_id=session["session_id"],
        query=stay["booking_id"],
    )

    assert any(
        item["booking_id"]
        == stay["booking_id"]
        for item in result["bookings"]
    )


def test_search_finds_case_by_category_and_summary(
    test_db,
):
    session = create_demo_session()
    stay = _stay(session)

    case = ensure_case(
        booking_id=stay["booking_id"],
        property_id=stay["property_id"],
        category="heating",
        summary="Boiler stopped heating the apartment.",
    )["case"]

    by_category = search_demo_session(
        session_id=session["session_id"],
        query="heating",
    )

    by_summary = search_demo_session(
        session_id=session["session_id"],
        query="boiler",
    )

    assert any(
        item["case_id"]
        == case["case_id"]
        for item in by_category["cases"]
    )

    assert any(
        item["case_id"]
        == case["case_id"]
        for item in by_summary["cases"]
    )


def test_search_is_session_scoped(
    test_db,
):
    first = create_demo_session()
    second = create_demo_session()

    second_stay = _stay(second)

    case = ensure_case(
        booking_id=second_stay["booking_id"],
        property_id=second_stay["property_id"],
        category="plumbing",
        summary="Unique second-session faucet issue.",
    )["case"]

    result = search_demo_session(
        session_id=first["session_id"],
        query="faucet",
    )

    assert all(
        item["case_id"]
        != case["case_id"]
        for item in result["cases"]
    )


def test_search_api_returns_session_results(
    test_db,
):
    session = create_demo_session()

    response = client.get(
        "/demo/sessions/search",
        params={"q": "Emma"},
        headers=_headers(session),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["query"] == "Emma"
    assert data["total"] >= 1
    assert len(data["guests"]) >= 1


def test_short_search_query_returns_empty_result(
    test_db,
):
    session = create_demo_session()

    result = search_demo_session(
        session_id=session["session_id"],
        query="E",
    )

    assert result["total"] == 0
    assert result["guests"] == []
    assert result["bookings"] == []
    assert result["cases"] == []
