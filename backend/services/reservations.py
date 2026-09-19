from .db import get_connection


def get_reservation(booking_id: str):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM bookings
            WHERE booking_id = ?
            """,
            (booking_id,),
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()


def get_guest_reservations(guest_id: str):
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM bookings
            WHERE guest_id = ?
            ORDER BY check_in
            """,
            (guest_id,),
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()