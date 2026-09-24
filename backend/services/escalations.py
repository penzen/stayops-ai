import uuid

from .db import get_connection
from backend.domain.enums import IssueCategory, Priority, CaseStatus




def create_escalation(
    booking_id: str | None,
    property_id: str,
    reason: str,
    category: str,
    priority: str = Priority.MEDIUM,
    incident_id: str | None = None,
    assigned_to: str | None = None,
):
    category = category.strip().lower()

    try:
        category = IssueCategory(category).value
    except ValueError:
        raise ValueError(
            f"Invalid escalation category: {category}"
        )
    
    try:
        priority = Priority(priority.strip().lower()).value
    except ValueError:
        raise ValueError(
            f"Invalid escalation priority: {priority}"
        )

    connection = get_connection()

    try:
        # If an incident is supplied, make sure it actually belongs
        # to this booking and property.
        if incident_id is not None:
            incident = connection.execute(
                """
                SELECT *
                FROM incidents
                WHERE incident_id = ?
                  AND booking_id IS ?
                  AND property_id = ?
                """,
                (
                    incident_id,
                    booking_id,
                    property_id,
                ),
            ).fetchone()

            if incident is None:
                raise ValueError(
                    "Incident does not belong to the supplied "
                    "booking and property."
                )

        escalation_id = f"esc_{uuid.uuid4().hex[:12]}"

        connection.execute(
            """
            INSERT INTO escalations (
                escalation_id,
                booking_id,
                property_id,
                incident_id,
                category,
                reason,
                priority,
                status,
                assigned_to
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                escalation_id,
                booking_id,
                property_id,
                incident_id,
                category,
                reason,
                priority,
                CaseStatus.OPEN,
                assigned_to,
            ),
        )

        connection.commit()

        row = connection.execute(
            """
            SELECT *
            FROM escalations
            WHERE escalation_id = ?
            """,
            (escalation_id,),
        ).fetchone()

        return dict(row)

    finally:
        connection.close()


def get_open_escalations():
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM escalations
            WHERE status = 'open'
            ORDER BY created_at DESC
            """
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


def find_existing_open_escalation(
    booking_id: str | None,
    property_id: str,
    category: str,
    incident_id: str | None = None,
):
    category = category.strip().lower()
    
    try:
        category = IssueCategory(category).value
    except ValueError:
        raise ValueError(
            f"Invalid escalation category: {category}"
        )

    
    connection = get_connection()

    try:
        # First try to find an escalation for the exact incident.
        if incident_id is not None:
            row = connection.execute(
                """
                SELECT e.*
                FROM escalations e
                JOIN incidents i
                  ON e.incident_id = i.incident_id
                WHERE e.incident_id = ?
                  AND e.category = ?
                  AND e.status = 'open'
                  AND i.booking_id IS ?
                  AND i.property_id = ?
                ORDER BY e.created_at DESC
                LIMIT 1
                """,
                (
                    incident_id,
                    category,
                    booking_id,
                    property_id,
                ),
            ).fetchone()

            if row is not None:
                return dict(row)

        # Otherwise find the same type of open escalation
        # for this booking and property.
        row = connection.execute(
            """
            SELECT *
            FROM escalations
            WHERE booking_id IS ?
              AND property_id = ?
              AND category = ?
              AND status = 'open'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (
                booking_id,
                property_id,
                category,
            ),
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()


def create_escalation_if_missing(
    booking_id: str | None,
    property_id: str,
    reason: str,
    category: str,
    priority: str = Priority.MEDIUM,
    incident_id: str | None = None,
    assigned_to: str | None = None,
):
    category = category.strip().lower()

    existing_escalation = find_existing_open_escalation(
        booking_id=booking_id,
        property_id=property_id,
        category=category,
        incident_id=incident_id,
    )

    if existing_escalation is not None:
        return {
            "created": False,
            "reason": "existing_open_escalation",
            "escalation": existing_escalation,
        }

    escalation = create_escalation(
        booking_id=booking_id,
        property_id=property_id,
        reason=reason,
        category=category,
        priority=priority,
        incident_id=incident_id,
        assigned_to=assigned_to,
    )

    return {
        "created": True,
        "reason": "escalation_created",
        "escalation": escalation,
    }