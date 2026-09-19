import uuid

from .db import get_connection


def get_open_incidents(property_id: str):
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM incidents
            WHERE property_id = ?
            AND status = 'open'
            ORDER BY created_at DESC
            """,
            (property_id,),
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


def create_incident(
    property_id: str,
    booking_id: str | None,
    category: str,
    description: str,
    severity: str = "medium",
):
    connection = get_connection()

    try:
        incident_id = f"inc_{uuid.uuid4().hex[:12]}"

        connection.execute(
            """
            INSERT INTO incidents (
                incident_id,
                property_id,
                booking_id,
                category,
                description,
                severity,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                incident_id,
                property_id,
                booking_id,
                category,
                description,
                severity,
                "open",
            ),
        )

        connection.commit()

        row = connection.execute(
            """
            SELECT *
            FROM incidents
            WHERE incident_id = ?
            """,
            (incident_id,),
        ).fetchone()

        return dict(row)

    finally:
        connection.close()


def resolve_incident(incident_id: str):
    connection = get_connection()

    try:
        connection.execute(
            """
            UPDATE incidents
            SET
                status = 'resolved',
                resolved_at = CURRENT_TIMESTAMP
            WHERE incident_id = ?
            """,
            (incident_id,),
        )

        connection.commit()

        row = connection.execute(
            """
            SELECT *
            FROM incidents
            WHERE incident_id = ?
            """,
            (incident_id,),
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()