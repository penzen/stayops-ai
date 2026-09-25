from backend.services.db import get_connection


DEMO_BOOKING_IDS = {
    "book_demo_current_001",
    "book_demo_en_001",
    "book_demo_de_001",
}


def get_demo_stays():
    """
    Return the demo stays available in the StayOps UI.
    """

    connection = get_connection()

    try:
        placeholders = ",".join(
            "?"
            for _ in DEMO_BOOKING_IDS
        )

        rows = connection.execute(
            f"""
            SELECT
                b.booking_id,
                b.guest_id,
                b.property_id,
                b.check_in,
                b.check_out,
                b.book_status,

                g.first_name,
                g.last_name,
                g.guest_lang,
                g.locale,

                p.title AS property_title

            FROM bookings AS b

            JOIN guests AS g
                ON g.guest_id = b.guest_id

            JOIN properties AS p
                ON p.property_id = b.property_id

            WHERE b.booking_id IN ({placeholders})

            ORDER BY
                g.first_name,
                g.last_name
            """,
            tuple(DEMO_BOOKING_IDS),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def reset_demo_state(
    booking_id: str,
):
    """
    Clear mutable operational state for one demo booking.

    Preserved:
    - guest
    - booking
    - property
    - access system

    Removed:
    - escalations
    - tasks
    - messages
    - incidents
    - compensation requests
    - cases
    """

    if booking_id not in DEMO_BOOKING_IDS:
        raise ValueError(
            "Booking is not a valid demo booking."
        )

    connection = get_connection()

    try:
        escalation_cursor = connection.execute(
            """
            DELETE FROM escalations
            WHERE booking_id = ?
            """,
            (booking_id,),
        )

        task_cursor = connection.execute(
            """
            DELETE FROM tasks
            WHERE booking_id = ?
            """,
            (booking_id,),
        )

        message_cursor = connection.execute(
            """
            DELETE FROM messages
            WHERE booking_id = ?
            """,
            (booking_id,),
        )

        incident_cursor = connection.execute(
            """
            DELETE FROM incidents
            WHERE booking_id = ?
            """,
            (booking_id,),
        )

        decision_cursor = connection.execute(
            """
            DELETE FROM compensation_decisions
            WHERE compensation_request_id IN (
                SELECT compensation_request_id
                FROM compensation_requests
                WHERE booking_id = ?
            )
            """,
            (booking_id,),
        )

        compensation_cursor = connection.execute(
            """
            DELETE FROM compensation_requests
            WHERE booking_id = ?
            """,
            (booking_id,),
        )

        event_cursor = connection.execute(
            """
            DELETE FROM case_events
            WHERE case_id IN (
                SELECT case_id
                FROM cases
                WHERE booking_id = ?
            )
            """,
            (booking_id,),
        )

        case_cursor = connection.execute(
            """
            DELETE FROM cases
            WHERE booking_id = ?
            """,
            (booking_id,),
        )

        connection.commit()

        return {
            "booking_id": booking_id,
            "status": "reset",
            "deleted": {
                "escalations":
                    escalation_cursor.rowcount,
                "tasks":
                    task_cursor.rowcount,
                "messages":
                    message_cursor.rowcount,
                "incidents":
                    incident_cursor.rowcount,
                "compensation_requests":
                    compensation_cursor.rowcount,
                "cases":
                    case_cursor.rowcount,
                "compensation_decisions":
                     decision_cursor.rowcount,
                "case_events":
                     event_cursor.rowcount,
            },
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()