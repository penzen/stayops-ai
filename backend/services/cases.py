import uuid

from backend.domain.enums import CaseStatus, IssueCategory
from .db import get_connection

ACTIVE_CASE_STATUSES = (
    CaseStatus.OPEN,
    CaseStatus.IN_PROGRESS,
    CaseStatus.WAITING_GUEST,
    CaseStatus.WAITING_HUMAN,
)

def find_existing_open_case(
    booking_id: str,
    property_id: str,
    category: str,
):
    category = category.strip().lower()

    try:
        category = IssueCategory(category).value
    except ValueError:
        raise ValueError(
            f"Invalid case category: {category}"
        )

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM cases
            WHERE booking_id = ?
            AND property_id = ?
            AND category = ?
            AND status IN (?, ?, ?, ?)
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (
                booking_id,
                property_id,
                category,
                CaseStatus.OPEN,
                CaseStatus.IN_PROGRESS,
                CaseStatus.WAITING_GUEST,
                CaseStatus.WAITING_HUMAN,
            ),
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()


def create_case(
    booking_id: str,
    property_id: str,
    category: str,
    summary: str | None = None,
):
    category = category.strip().lower()

    try:
        category = IssueCategory(category).value
    except ValueError:
        raise ValueError(
            f"Invalid case category: {category}"
        )

    connection = get_connection()

    try:
        booking = connection.execute(
            """
            SELECT booking_id, property_id
            FROM bookings
            WHERE booking_id = ?
            """,
            (booking_id,),
        ).fetchone()

        if booking is None:
            raise ValueError(
                f"Booking does not exist: {booking_id}"
            )

        if booking["property_id"] != property_id:
            raise ValueError(
                "Property does not belong to the supplied booking."
            )

        case_id = f"case_{uuid.uuid4().hex[:12]}"

        connection.execute(
            """
            INSERT INTO cases (
                case_id,
                booking_id,
                property_id,
                category,
                status,
                summary
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                case_id,
                booking_id,
                property_id,
                category,
                CaseStatus.OPEN,
                summary,
            ),
        )

        connection.commit()

        row = connection.execute(
            """
            SELECT *
            FROM cases
            WHERE case_id = ?
            """,
            (case_id,),
        ).fetchone()

        return dict(row)

    finally:
        connection.close()


def ensure_case(
    booking_id: str,
    property_id: str,
    category: str,
    summary: str | None = None,
):
    existing_case = find_existing_open_case(
        booking_id=booking_id,
        property_id=property_id,
        category=category,
    )

    if existing_case is not None:
        return {
            "created": False,
            "reason": "existing_open_case",
            "case": existing_case,
        }

    case = create_case(
        booking_id=booking_id,
        property_id=property_id,
        category=category,
        summary=summary,
    )

    return {
        "created": True,
        "reason": "case_created",
        "case": case,
    }

def get_case(case_id: str):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM cases
            WHERE case_id = ?
            """,
            (case_id,),
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()

def get_open_cases_for_booking(booking_id: str):
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM cases
            WHERE booking_id = ?
            AND status IN (?, ?, ?, ?)
            ORDER BY created_at DESC
            """,
            (
                booking_id,
                CaseStatus.OPEN,
                CaseStatus.IN_PROGRESS,
                CaseStatus.WAITING_GUEST,
                CaseStatus.WAITING_HUMAN,
            ),
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()

def get_case_context(
    case_id: str,
    recent_message_limit: int = 10,
):
    """
    Build a deterministic operational snapshot for a Case.

    The Case owns tasks and escalations directly.
    Messages remain booking-level because one guest message
    can relate to multiple Cases.
    """

    connection = get_connection()

    try:
        case = connection.execute(
            """
            SELECT *
            FROM cases
            WHERE case_id = ?
            """,
            (case_id,),
        ).fetchone()

        if case is None:
            return None

        case = dict(case)

        tasks = connection.execute(
            """
            SELECT *
            FROM tasks
            WHERE case_id = ?
            ORDER BY task_date ASC
            """,
            (case_id,),
        ).fetchall()

        escalations = connection.execute(
            """
            SELECT *
            FROM escalations
            WHERE case_id = ?
            ORDER BY created_at ASC
            """,
            (case_id,),
        ).fetchall()

        recent_messages = connection.execute(
            """
            SELECT *
            FROM messages
            WHERE booking_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (
                case["booking_id"],
                recent_message_limit,
            ),
        ).fetchall()

        return {
            "case": case,
            "tasks": [
                dict(task)
                for task in tasks
            ],
            "escalations": [
                dict(escalation)
                for escalation in escalations
            ],
            "recent_messages": [
                dict(message)
                for message in reversed(recent_messages)
            ],
        }

    finally:
        connection.close()

CASE_TRANSITIONS = {
    CaseStatus.OPEN: {
        CaseStatus.IN_PROGRESS,
        CaseStatus.WAITING_GUEST,
        CaseStatus.WAITING_HUMAN,
        CaseStatus.RESOLVED,
    },
    CaseStatus.IN_PROGRESS: {
        CaseStatus.WAITING_GUEST,
        CaseStatus.WAITING_HUMAN,
        CaseStatus.RESOLVED,
    },
    CaseStatus.WAITING_GUEST: {
        CaseStatus.IN_PROGRESS,
        CaseStatus.WAITING_HUMAN,
        CaseStatus.RESOLVED,
    },
    CaseStatus.WAITING_HUMAN: {
        CaseStatus.IN_PROGRESS,
        CaseStatus.WAITING_GUEST,
        CaseStatus.RESOLVED,
    },
    CaseStatus.RESOLVED: set(),
}

def transition_case_status(
    case_id: str,
    new_status: str,
):
    try:
        new_status = CaseStatus(
            new_status.strip().lower()
        )
    except ValueError:
        raise ValueError(
            f"Invalid Case status: {new_status}"
        )

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM cases
            WHERE case_id = ?
            """,
            (case_id,),
        ).fetchone()

        if row is None:
            raise ValueError(
                f"Case does not exist: {case_id}"
            )

        case = dict(row)

        current_status = CaseStatus(
            case["status"]
        )

        if current_status == new_status:
            return {
                "transitioned": False,
                "reason": "already_in_status",
                "from_status": current_status.value,
                "to_status": new_status.value,
                "case": case,
            }

        allowed_statuses = CASE_TRANSITIONS[
            current_status
        ]

        if new_status not in allowed_statuses:
            raise ValueError(
                "Invalid Case transition: "
                f"{current_status.value} "
                f"-> {new_status.value}"
            )

        if new_status == CaseStatus.RESOLVED:
            connection.execute(
                """
                UPDATE cases
                SET status = ?,
                    resolved_at = CURRENT_TIMESTAMP
                WHERE case_id = ?
                """,
                (
                    new_status.value,
                    case_id,
                ),
            )
        else:
            connection.execute(
                """
                UPDATE cases
                SET status = ?
                WHERE case_id = ?
                """,
                (
                    new_status.value,
                    case_id,
                ),
            )

        connection.commit()

        updated_row = connection.execute(
            """
            SELECT *
            FROM cases
            WHERE case_id = ?
            """,
            (case_id,),
        ).fetchone()

        return {
            "transitioned": True,
            "reason": "status_transitioned",
            "from_status": current_status.value,
            "to_status": new_status.value,
            "case": dict(updated_row),
        }

    finally:
        connection.close()

"""
get_case_context(case_id)

        ↓

{
    case: {...},

    tasks: [
        everything this Case has caused
    ],

    escalations: [
        human handoffs for this Case
    ],

    recent_messages: [
        recent booking conversation
    ]
}

"""