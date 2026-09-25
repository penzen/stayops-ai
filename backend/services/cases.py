import uuid
from .audit import record_case_event
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
        record_case_event(
            case_id=case_id,
            event_type="case_created",
            actor_type="system",
            actor_id="case_service",
            summary=f"{category.capitalize()} Case created.",
            metadata={
                "booking_id": booking_id,
                "property_id": property_id,
                "category": category,
            },
            connection=connection,
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

def claim_case(
    case_id: str,
    operator_id: str,
):
    """
    Claim a Case that is waiting for human intervention.

    Claiming records human ownership but does not itself
    complete any operational work or resolve the Case.
    """

    operator_id = operator_id.strip()

    if not operator_id:
        raise ValueError(
            "Operator ID is required."
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

        if case["status"] != CaseStatus.WAITING_HUMAN:
            raise ValueError(
                "Case must be waiting_human "
                "before it can be claimed."
            )

        operator = connection.execute(
            """
            SELECT team_id
            FROM teams
            WHERE team_id = ?
            """,
            (operator_id,),
        ).fetchone()

        if operator is None:
            raise ValueError(
                f"Operator does not exist: {operator_id}"
            )

        if case["assigned_to"] == operator_id:
            return {
                "claimed": False,
                "reason": "already_claimed_by_operator",
                "case": case,
            }

        if case["assigned_to"] is not None:
            raise ValueError(
                "Case is already claimed "
                "by another operator."
            )

        connection.execute(
            """
            UPDATE cases
            SET
                assigned_to = ?,
                claimed_at = CURRENT_TIMESTAMP
            WHERE case_id = ?
            """,
            (
                operator_id,
                case_id,
            ),
        )
        record_case_event(
            case_id=case_id,
            event_type="case_claimed",
            actor_type="human",
            actor_id=operator_id,
            summary="Operator claimed the Case.",
            metadata={
                "operator_id": operator_id,
            },
            connection=connection,
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
            "claimed": True,
            "reason": "case_claimed",
            "case": dict(updated_row),
        }

    finally:
        connection.close()

def return_case_to_agent(
    case_id: str,
    operator_id: str,
):
    """
    Return a human-owned Case to autonomous agent workflow.

    Control may return only when the Case is waiting_human,
    is owned by the supplied operator, and no Case-linked
    task or escalation remains open.
    """

    operator_id = operator_id.strip()

    if not operator_id:
        raise ValueError(
            "Operator ID is required."
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

        if case["status"] != CaseStatus.WAITING_HUMAN:
            raise ValueError(
                "Case must be waiting_human "
                "before it can return to the agent."
            )

        if case["assigned_to"] is None:
            raise ValueError(
                "Case must be claimed before it "
                "can return to the agent."
            )

        if case["assigned_to"] != operator_id:
            raise ValueError(
                "Only the assigned operator can "
                "return this Case to the agent."
            )

        open_tasks = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM tasks
            WHERE case_id = ?
              AND task_status = 'open'
            """,
            (case_id,),
        ).fetchone()["count"]

        open_escalations = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM escalations
            WHERE case_id = ?
              AND status = 'open'
            """,
            (case_id,),
        ).fetchone()["count"]

        if open_tasks > 0 or open_escalations > 0:
            raise ValueError(
                "Case still has open human work "
                "and cannot return to the agent."
            )

        connection.execute(
            """
            UPDATE cases
            SET
                status = ?,
                assigned_to = NULL,
                claimed_at = NULL
            WHERE case_id = ?
            """,
            (
                CaseStatus.IN_PROGRESS,
                case_id,
            ),
        )
        record_case_event(
            case_id=case_id,
            event_type="case_returned_to_agent",
            actor_type="human",
            actor_id=operator_id,
            summary="Operator returned control to the agent.",
            metadata={
                "operator_id": operator_id,
                "from_status": CaseStatus.WAITING_HUMAN.value,
                "to_status": CaseStatus.IN_PROGRESS.value,
            },
            connection=connection,
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
            "returned": True,
            "reason": "case_returned_to_agent",
            "open_tasks": 0,
            "open_escalations": 0,
            "case": dict(updated_row),
        }

    finally:
        connection.close()


def get_human_operations_queue():
    """
    Return active Cases currently blocked on human action.

    The queue is a read-only operational projection built
    from existing Case, booking, guest, property, task,
    escalation, and team state.
    """

    connection = get_connection()

    try:
        case_rows = connection.execute(
            """
            SELECT *
            FROM cases
            WHERE status = ?
            ORDER BY created_at ASC
            """,
            (CaseStatus.WAITING_HUMAN,),
        ).fetchall()

        queue = []

        for case_row in case_rows:
            case = dict(case_row)

            booking_row = connection.execute(
                """
                SELECT *
                FROM bookings
                WHERE booking_id = ?
                """,
                (case["booking_id"],),
            ).fetchone()

            booking = (
                dict(booking_row)
                if booking_row is not None
                else None
            )

            guest = None

            if booking is not None:
                guest_row = connection.execute(
                    """
                    SELECT *
                    FROM guests
                    WHERE guest_id = ?
                    """,
                    (booking["guest_id"],),
                ).fetchone()

                if guest_row is not None:
                    guest = dict(guest_row)

            property_row = connection.execute(
                """
                SELECT *
                FROM properties
                WHERE property_id = ?
                """,
                (case["property_id"],),
            ).fetchone()

            property_data = (
                dict(property_row)
                if property_row is not None
                else None
            )

            task_rows = connection.execute(
                """
                SELECT *
                FROM tasks
                WHERE case_id = ?
                ORDER BY task_date ASC
                """,
                (case["case_id"],),
            ).fetchall()

            tasks = [
                dict(row)
                for row in task_rows
            ]

            escalation_rows = connection.execute(
                """
                SELECT *
                FROM escalations
                WHERE case_id = ?
                ORDER BY created_at ASC
                """,
                (case["case_id"],),
            ).fetchall()

            escalations = [
                dict(row)
                for row in escalation_rows
            ]

            operator = None

            if case["assigned_to"] is not None:
                operator_row = connection.execute(
                    """
                    SELECT *
                    FROM teams
                    WHERE team_id = ?
                    """,
                    (case["assigned_to"],),
                ).fetchone()

                if operator_row is not None:
                    operator = dict(operator_row)

            open_escalations = [
                escalation
                for escalation in escalations
                if escalation["status"] == "open"
            ]

            latest_open_escalation = (
                open_escalations[-1]
                if open_escalations
                else None
            )

            handoff = {
                "reason": (
                    latest_open_escalation["reason"]
                    if latest_open_escalation
                    else None
                ),
                "priority": (
                    latest_open_escalation["priority"]
                    if latest_open_escalation
                    else None
                ),
                "assigned_to": case["assigned_to"],
                "claimed_at": case["claimed_at"],
            }

            queue.append(
                {
                    "case": case,
                    "booking": booking,
                    "guest": guest,
                    "property": property_data,
                    "tasks": tasks,
                    "escalations": escalations,
                    "operator": operator,
                    "handoff": handoff,
                }
            )

        return queue

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
    },
    CaseStatus.IN_PROGRESS: {
        CaseStatus.WAITING_GUEST,
        CaseStatus.WAITING_HUMAN,
    },
    CaseStatus.WAITING_GUEST: {
        CaseStatus.IN_PROGRESS,
        CaseStatus.WAITING_HUMAN,
    },
    CaseStatus.WAITING_HUMAN: {
        CaseStatus.IN_PROGRESS,
        CaseStatus.WAITING_GUEST,
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
        record_case_event(
            case_id=case_id,
            event_type="case_status_changed",
            actor_type="system",
            actor_id="case_service",
            summary=(
                "Case status changed from "
                f"{current_status.value} to {new_status.value}."
            ),
            metadata={
                "from_status": current_status.value,
                "to_status": new_status.value,
            },
            connection=connection,
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

def resolve_case_if_ready(case_id: str):
    """
    Resolve a Case only when deterministic operational evidence
    shows that no linked work remains open.

    A Case cannot resolve merely because the agent believes the
    issue is finished.
    """

    connection = get_connection()

    try:
        case_row = connection.execute(
            """
            SELECT *
            FROM cases
            WHERE case_id = ?
            """,
            (case_id,),
        ).fetchone()

        if case_row is None:
            raise ValueError(
                f"Case does not exist: {case_id}"
            )

        case = dict(case_row)

        # Idempotent resolution.
        if case["status"] == CaseStatus.RESOLVED:
            return {
                "resolved": True,
                "reason": "already_resolved",
                "open_tasks": 0,
                "open_escalations": 0,
                "case": case,
            }

        task_counts = connection.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(
                    CASE
                        WHEN task_status = 'open'
                        THEN 1
                        ELSE 0
                    END
                ) AS open_count
            FROM tasks
            WHERE case_id = ?
            """,
            (case_id,),
        ).fetchone()

        escalation_counts = connection.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(
                    CASE
                        WHEN status = 'open'
                        THEN 1
                        ELSE 0
                    END
                ) AS open_count
            FROM escalations
            WHERE case_id = ?
            """,
            (case_id,),
        ).fetchone()

        total_tasks = task_counts["total"]
        open_tasks = task_counts["open_count"] or 0

        total_escalations = escalation_counts["total"]
        open_escalations = (
            escalation_counts["open_count"] or 0
        )

        total_evidence = (
            total_tasks + total_escalations
        )

        # A Case with no operational records has no deterministic
        # evidence that anything was actually resolved.
        if total_evidence == 0:
            return {
                "resolved": False,
                "reason": "no_resolution_evidence",
                "open_tasks": 0,
                "open_escalations": 0,
                "case": case,
            }

        # Any still-open work blocks Case resolution.
        if open_tasks > 0 or open_escalations > 0:
            return {
                "resolved": False,
                "reason": "unresolved_operational_work",
                "open_tasks": open_tasks,
                "open_escalations": open_escalations,
                "case": case,
            }

        # ---------------------------------------------------------
        # REFUND CASE FINANCIAL RESOLUTION GATE
        # ---------------------------------------------------------

        if case["category"] == IssueCategory.REFUND:
            compensation_request = connection.execute(
                """
                SELECT *
                FROM compensation_requests
                WHERE case_id = ?
                """,
                (case_id,),
            ).fetchone()

            if compensation_request is None:
                return {
                    "resolved": False,
                    "reason": "compensation_request_missing",
                    "open_tasks": open_tasks,
                    "open_escalations": open_escalations,
                    "case": case,
                }

            compensation_request = dict(
                compensation_request
            )

            decision = connection.execute(
                """
                SELECT *
                FROM compensation_decisions
                WHERE compensation_request_id = ?
                """,
                (
                    compensation_request[
                        "compensation_request_id"
                    ],
                ),
            ).fetchone()

            if decision is None:
                return {
                    "resolved": False,
                    "reason": "financial_decision_pending",
                    "open_tasks": open_tasks,
                    "open_escalations": open_escalations,
                    "case": case,
                }

        connection.execute(
            """
            UPDATE cases
            SET status = ?,
                resolved_at = CURRENT_TIMESTAMP
            WHERE case_id = ?
            """,
            (
                CaseStatus.RESOLVED,
                case_id,
            ),
        )
        record_case_event(
            case_id=case_id,
            event_type="case_resolved",
            actor_type="system",
            actor_id="case_resolution_service",
            summary="Case resolution verified and Case resolved.",
            metadata={
                "from_status": case["status"],
                "to_status": CaseStatus.RESOLVED.value,
                "open_tasks": 0,
                "open_escalations": 0,
            },
            connection=connection,
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
            "resolved": True,
            "reason": "case_resolved",
            "open_tasks": 0,
            "open_escalations": 0,
            "case": dict(updated_row),
        }

    finally:
        connection.close()


def get_recent_cases_for_booking(
    booking_id: str,
    category: str | None = None,
    limit: int = 5,
):
    """
    Retrieve recent Cases for a booking, including resolved Cases.

    This is intended for historical follow-up questions where an
    issue may already have completed its workflow.
    """

    if limit <= 0:
        raise ValueError(
            "Case history limit must be greater than zero."
        )

    normalized_category = None

    if category is not None:
        normalized_category = category.strip().lower()

        try:
            normalized_category = IssueCategory(
                normalized_category
            ).value
        except ValueError:
            raise ValueError(
                f"Invalid case category: {category}"
            )

    connection = get_connection()

    try:
        if normalized_category is None:
            rows = connection.execute(
                """
                SELECT *
                FROM cases
                WHERE booking_id = ?
                ORDER BY created_at DESC, rowid DESC
                LIMIT ?
                """,
                (
                    booking_id,
                    limit,
                ),
            ).fetchall()

        else:
            rows = connection.execute(
                """
                SELECT *
                FROM cases
                WHERE booking_id = ?
                AND category = ?
                ORDER BY created_at DESC, rowid DESC
                LIMIT ?
                """,
                (
                    booking_id,
                    normalized_category,
                    limit,
                ),
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

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