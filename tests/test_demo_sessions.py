import sqlite3
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.services.demo_guests import (
    create_demo_guest_stay,
)
from backend.services.demo_sessions import (
    DemoSessionExpired,
    cleanup_expired_demo_sessions,
    create_demo_session,
    get_demo_session_stays,
    require_demo_booking_access,
    validate_demo_session,
)


client = TestClient(app)


def _session_headers(token: str):
    return {
        "X-StayOps-Demo-Token": token,
    }


def test_create_demo_session_clones_sample_stays(
    test_db,
):
    result = create_demo_session()

    assert result["session_id"].startswith(
        "dms_"
    )
    assert result["session_token"]
    assert len(result["sample_stays"]) == 3

    booking_ids = {
        stay["booking_id"]
        for stay in result["sample_stays"]
    }

    assert len(booking_ids) == 3
    assert all(
        booking_id.startswith(
            "book_demo_session_"
        )
        for booking_id in booking_ids
    )


def test_two_demo_sessions_have_disjoint_bookings(
    test_db,
):
    first = create_demo_session()
    second = create_demo_session()

    first_ids = {
        stay["booking_id"]
        for stay in first["sample_stays"]
    }
    second_ids = {
        stay["booking_id"]
        for stay in second["sample_stays"]
    }

    assert first_ids.isdisjoint(
        second_ids
    )


def test_session_token_validates_and_booking_access_is_scoped(
    test_db,
):
    first = create_demo_session()
    second = create_demo_session()

    validated = validate_demo_session(
        first["session_token"]
    )

    assert (
        validated["session_id"]
        == first["session_id"]
    )

    first_booking = (
        first["sample_stays"][0][
            "booking_id"
        ]
    )

    require_demo_booking_access(
        session_id=first["session_id"],
        booking_id=first_booking,
    )

    with pytest.raises(ValueError):
        require_demo_booking_access(
            session_id=second["session_id"],
            booking_id=first_booking,
        )


def test_custom_stay_can_be_registered_to_session(
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

    stays = get_demo_session_stays(
        session["session_id"]
    )

    created_stay = next(
        stay
        for stay in stays
        if (
            stay["booking_id"]
            == created["booking_id"]
        )
    )

    assert (
        created_stay["resource_kind"]
        == "custom"
    )


def test_expired_demo_session_is_cleaned_up(
    test_db,
):
    session = create_demo_session()

    connection = sqlite3.connect(
        test_db
    )

    try:
        expired = (
            datetime.now(timezone.utc)
            - timedelta(hours=1)
        ).replace(
            tzinfo=None,
            microsecond=0,
        ).isoformat(
            sep=" "
        )

        connection.execute(
            """
            UPDATE demo_sessions
            SET expires_at = ?
            WHERE session_id = ?
            """,
            (
                expired,
                session["session_id"],
            ),
        )
        connection.commit()

    finally:
        connection.close()

    with pytest.raises(
        DemoSessionExpired
    ):
        validate_demo_session(
            session["session_token"]
        )

    cleanup = (
        cleanup_expired_demo_sessions()
    )

    assert (
        cleanup["deleted_sessions"]
        == 1
    )

    connection = sqlite3.connect(
        test_db
    )

    try:
        session_count = (
            connection.execute(
                """
                SELECT COUNT(*)
                FROM demo_sessions
                """
            ).fetchone()[0]
        )

        booking_count = (
            connection.execute(
                """
                SELECT COUNT(*)
                FROM bookings
                WHERE booking_id LIKE
                    'book_demo_session_%'
                """
            ).fetchone()[0]
        )

        assert session_count == 0
        assert booking_count == 0

    finally:
        connection.close()


def test_demo_session_api_returns_scoped_stays(
    test_db,
):
    response = client.post(
        "/demo/sessions"
    )

    assert response.status_code == 201

    session = response.json()

    stays_response = client.get(
        "/demo/sessions/stays",
        headers=_session_headers(
            session["session_token"]
        ),
    )

    assert stays_response.status_code == 200

    stays = stays_response.json()

    assert len(stays) == 3
    assert all(
        stay["booking_id"].startswith(
            "book_demo_session_"
        )
        for stay in stays
    )
