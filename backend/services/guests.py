from .db import get_connection


def get_guest(guest_id: str):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM guests
            WHERE guest_id = ?
            """,
            (guest_id,),
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()