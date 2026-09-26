import uuid

from .db import get_connection
from backend.domain.enums import IssueCategory, Priority, CaseStatus

from .audit import record_case_event


def create_escalation(
    booking_id: str | None,
    property_id: str,
    reason: str,
    category: str,
    priority: str = Priority.MEDIUM,
    incident_id: str | None = None,
    assigned_to: str | None = None,
    case_id: str | None = None,
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
                assigned_to,
                case_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                case_id,
            ),
        )
        if case_id is not None:
            record_case_event(
                case_id=case_id,
                event_type="escalation_created",
                actor_type="agent",
                actor_id="guest_ops_agent",
                summary="Human escalation created.",
                metadata={
                    "escalation_id": escalation_id,
                    "category": category,
                    "priority": priority,
                    "reason": reason,
                },
                connection=connection,
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
    case_id: str | None = None,
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
        # -----------------------------------------------------
        # V3 CASE-AWARE LOOKUP
        # -----------------------------------------------------

        if case_id is not None:
            # First: does this Case already own an open
            # escalation for this category?
            row = connection.execute(
                """
                SELECT *
                FROM escalations
                WHERE case_id = ?
                  AND category = ?
                  AND status = 'open'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (
                    case_id,
                    category,
                ),
            ).fetchone()

            if row is not None:
                return dict(row)

            # Second: if an incident is supplied, allow adoption
            # of an equivalent legacy escalation that is not yet
            # owned by any Case.
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
                      AND e.case_id IS NULL
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

            # Third: allow adoption of a matching legacy
            # escalation for the same operational issue.
            row = connection.execute(
                """
                SELECT *
                FROM escalations
                WHERE booking_id IS ?
                  AND property_id = ?
                  AND category = ?
                  AND status = 'open'
                  AND case_id IS NULL
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

        # -----------------------------------------------------
        # LEGACY / NON-CASE LOOKUP
        # -----------------------------------------------------

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
    case_id: str | None = None,
):
    category = category.strip().lower()

    existing_escalation = find_existing_open_escalation(
        booking_id=booking_id,
        property_id=property_id,
        category=category,
        incident_id=incident_id,
        case_id=case_id,
    )

    if existing_escalation is not None:
        if (
            case_id is not None
            and existing_escalation["case_id"] is None
        ):
            connection = get_connection()

            try:
                connection.execute(
                    """
                    UPDATE escalations
                    SET case_id = ?
                    WHERE escalation_id = ?
                    AND case_id IS NULL
                    """,
                    (
                        case_id,
                        existing_escalation["escalation_id"],
                    ),
                )

                connection.commit()

                row = connection.execute(
                    """
                    SELECT *
                    FROM escalations
                    WHERE escalation_id = ?
                    """,
                    (existing_escalation["escalation_id"],),
                ).fetchone()

                existing_escalation = dict(row)

            finally:
                connection.close()

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
        case_id=case_id,
    )

    return {
        "created": True,
        "reason": "escalation_created",
        "escalation": escalation,
    }

def resolve_escalation(escalation_id: str, operator_id: str | None = None,):
    """
    Mark a human escalation as resolved.

    This represents evidence that the human handoff
    no longer requires action.
    """

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM escalations
            WHERE escalation_id = ?
            """,
            (escalation_id,),
        ).fetchone()

        if row is None:
            return None

        escalation = dict(row)
        # -----------------------------------------------------
        # HUMAN AUTHORIZATION
        # -----------------------------------------------------

        authorized_operator_id = None

        if operator_id is not None:
            operator_id = operator_id.strip()

            if not operator_id:
                raise ValueError(
                    "Operator ID is required."
                )

            if escalation["case_id"] is None:
                raise ValueError(
                    "Escalation must belong to a Case "
                    "before human resolution."
                )

            case_row = connection.execute(
                """
                SELECT *
                FROM cases
                WHERE case_id = ?
                """,
                (escalation["case_id"],),
            ).fetchone()

            if case_row is None:
                raise ValueError(
                    "Case does not exist: "
                    f"{escalation['case_id']}"
                )

            case = dict(case_row)

            if case["status"] != CaseStatus.WAITING_HUMAN:
                raise ValueError(
                    "Case must be waiting_human "
                    "before human escalation resolution."
                )

            if case["assigned_to"] is None:
                raise ValueError(
                    "Case must be claimed before "
                    "resolving human escalation work."
                )

            if case["assigned_to"] != operator_id:
                raise ValueError(
                    "Only the assigned Case operator "
                    "can resolve this escalation."
                )

            authorized_operator_id = operator_id

        if escalation["status"] == CaseStatus.RESOLVED:
            return escalation

        connection.execute(
            """
            UPDATE escalations
            SET
                status = ?,
                resolved_at = CURRENT_TIMESTAMP
            WHERE escalation_id = ?
            """,
            (
                CaseStatus.RESOLVED,
                escalation_id,
            ),
        )
        if escalation["case_id"] is not None:
            record_case_event(
                case_id=escalation["case_id"],
                event_type="escalation_resolved",
                actor_type=(
                    "human"
                    if authorized_operator_id is not None
                    else "system"
                ),
                actor_id=(
                    authorized_operator_id
                    if authorized_operator_id is not None
                    else "escalation_service"
                ),
                summary="Human escalation resolved.",
                metadata={
                    "escalation_id": escalation_id,
                    "category": escalation["category"],
                    "priority": escalation["priority"],
                },
                connection=connection,
            )

        connection.commit()

        updated_row = connection.execute(
            """
            SELECT *
            FROM escalations
            WHERE escalation_id = ?
            """,
            (escalation_id,),
        ).fetchone()

        return dict(updated_row)

    finally:
        connection.close()