from datetime import datetime, timedelta

from backend.services.access_rules import verify_guest_access
from backend.services.db import get_connection


GUEST_ID = "gst_2631"
BOOKING_ID = "book_demo_current_001"


def set_booking_window(check_in: datetime, check_out: datetime):
    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE bookings
            SET check_in = ?,
                check_out = ?,
                book_status = 'confirmed'
            WHERE booking_id = ?
            """,
            (
                check_in.isoformat(sep=" "),
                check_out.isoformat(sep=" "),
                BOOKING_ID,
            ),
        )
        connection.commit()

    finally:
        connection.close()


def test_access_allowed_during_active_stay(test_db):
    now = datetime.now()

    set_booking_window(
        check_in=now - timedelta(days=1),
        check_out=now + timedelta(days=1),
    )

    result = verify_guest_access(
        guest_id=GUEST_ID,
        booking_id=BOOKING_ID,
    )

    assert result["allowed"] is True
    assert result["reason"] == "access_verified"
    assert result["guest_id"] == GUEST_ID
    assert result["booking_id"] == BOOKING_ID


def test_access_denied_outside_stay_window(test_db):
    now = datetime.now()

    set_booking_window(
        check_in=now - timedelta(days=3),
        check_out=now - timedelta(days=2),
    )

    result = verify_guest_access(
        guest_id=GUEST_ID,
        booking_id=BOOKING_ID,
    )

    assert result["allowed"] is False
    assert result["reason"] == "outside_valid_stay_window"


"""
Test 1
booking = yesterday → tomorrow
              ↓
       verify_guest_access()
              ↓
          allowed ✓


Test 2
booking = 3 days ago → 2 days ago
              ↓
       verify_guest_access()
              ↓
          denied ✓

"""