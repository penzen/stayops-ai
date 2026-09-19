import uuid

from .db import get_connection


def send_message(
    booking_id: str,
    guest_id: str,
    sender_type: str,
    message_text: str,
    channel: str = "chat",
):
    connection = get_connection()

    try:
        message_id = f"msg_{uuid.uuid4().hex[:12]}"

        connection.execute(
            """
            INSERT INTO messages (
                message_id,
                booking_id,
                guest_id,
                sender_type,
                message_text,
                channel
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                message_id,
                booking_id,
                guest_id,
                sender_type,
                message_text,
                channel,
            ),
        )

        connection.commit()

        row = connection.execute(
            """
            SELECT *
            FROM messages
            WHERE message_id = ?
            """,
            (message_id,),
        ).fetchone()

        return dict(row)

    finally:
        connection.close()


def get_booking_messages(booking_id: str):
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM messages
            WHERE booking_id = ?
            ORDER BY created_at ASC
            """,
            (booking_id,),
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()