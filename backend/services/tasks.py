import uuid
from datetime import datetime

from .db import get_connection
from .audit import record_case_event

def create_task(
    property_id: str,
    booking_id: str | None,
    category: str,
    title: str,
    assigned_by: str = "AI_AGENT",
    assigned_to: str | None = None,
    parent_task_id: str | None = None,
    case_id: str | None = None,
):
    connection = get_connection()

    try:
        task_id = f"task_{uuid.uuid4().hex[:12]}"

        task_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        connection.execute(
            """
            INSERT INTO tasks (
                task_id,
                property_id,
                booking_id,
                category,
                title,
                task_date,
                task_status,
                assigned_by,
                assigned_to,
                parent_task_id,
                case_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                task_id,
                property_id,
                booking_id,
                category,
                title,
                task_date,
                "open",
                assigned_by,
                assigned_to,
                parent_task_id,
                case_id,
            ),
        )
        if case_id is not None:
            record_case_event(
                case_id=case_id,
                event_type="task_created",
                actor_type=(
                    "agent"
                    if assigned_by == "AI_AGENT"
                    else "human"
                ),
                actor_id=assigned_by,
                summary="Operational task created.",
                metadata={
                    "task_id": task_id,
                    "category": category,
                    "title": title,
                    "assigned_to": assigned_to,
                },
                connection=connection,
            )

        connection.commit()

        row = connection.execute(
            """
            SELECT *
            FROM tasks
            WHERE task_id = ?
            """,
            (task_id,),
        ).fetchone()

        return dict(row)

    finally:
        connection.close()


def get_open_tasks(property_id: str):
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM tasks
            WHERE property_id = ?
            AND task_status = 'open'
            ORDER BY task_date DESC
            """,
            (property_id,),
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()



def find_existing_open_task(
    property_id: str,
    booking_id: str | None,
    category: str,
    case_id: str | None = None,
):
    """
    Find an existing open task for the same Case.

    If a Case is supplied and no Case-linked task exists,
    allow reuse of a matching legacy task that has not yet
    been linked to any Case.
    """

    connection = get_connection()

    try:
        if case_id is not None:
            row = connection.execute(
                """
                SELECT *
                FROM tasks
                WHERE case_id = ?
                  AND task_status = 'open'
                ORDER BY task_date DESC
                LIMIT 1
                """,
                (case_id,),
            ).fetchone()

            if row is not None:
                return dict(row)

            row = connection.execute(
                """
                SELECT *
                FROM tasks
                WHERE property_id = ?
                  AND booking_id IS ?
                  AND LOWER(category) = LOWER(?)
                  AND task_status = 'open'
                  AND case_id IS NULL
                ORDER BY task_date DESC
                LIMIT 1
                """,
                (
                    property_id,
                    booking_id,
                    category,
                ),
            ).fetchone()

            if row is None:
                return None

            return dict(row)

        row = connection.execute(
            """
            SELECT *
            FROM tasks
            WHERE property_id = ?
              AND booking_id IS ?
              AND LOWER(category) = LOWER(?)
              AND task_status = 'open'
            ORDER BY task_date DESC
            LIMIT 1
            """,
            (
                property_id,
                booking_id,
                category,
            ),
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()


def create_task_if_missing(
    property_id: str,
    booking_id: str | None,
    category: str,
    title: str,
    assigned_by: str = "AI_AGENT",
    assigned_to: str | None = None,
    parent_task_id: str | None = None,
    case_id: str | None = None,
):
    """
    Create a task only when an equivalent open operational
    task does not already exist.
    """

    existing_task = find_existing_open_task(
        property_id=property_id,
        booking_id=booking_id,
        category=category,
        case_id=case_id,
    )

    if existing_task is not None:
        if (
            case_id is not None
            and existing_task["case_id"] is None
        ):
            connection = get_connection()

            try:
                connection.execute(
                    """
                    UPDATE tasks
                    SET case_id = ?
                    WHERE task_id = ?
                    AND case_id IS NULL
                    """,
                    (
                        case_id,
                        existing_task["task_id"],
                    ),
                )

                connection.commit()

                row = connection.execute(
                    """
                    SELECT *
                    FROM tasks
                    WHERE task_id = ?
                    """,
                    (existing_task["task_id"],),
                ).fetchone()

                existing_task = dict(row)

            finally:
                connection.close()

        return {
            "created": False,
            "reason": "existing_open_task",
            "task": existing_task,
        }

    task = create_task(
        property_id=property_id,
        booking_id=booking_id,
        category=category,
        title=title,
        assigned_by=assigned_by,
        assigned_to=assigned_to,
        parent_task_id=parent_task_id,
        case_id=case_id,
    )

    return {
        "created": True,
        "reason": "task_created",
        "task": task,
    }

def complete_task(task_id: str):
    """
    Mark an operational task as completed.

    This represents deterministic evidence that the task
    itself no longer requires operational work.
    """

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM tasks
            WHERE task_id = ?
            """,
            (task_id,),
        ).fetchone()

        if row is None:
            return None

        task = dict(row)

        if task["task_status"] == "completed":
            return task

        connection.execute(
            """
            UPDATE tasks
            SET task_status = 'completed'
            WHERE task_id = ?
            """,
            (task_id,),
        )
        if task["case_id"] is not None:
            case_row = connection.execute(
                """
                SELECT assigned_to
                FROM cases
                WHERE case_id = ?
                """,
                (task["case_id"],),
            ).fetchone()

            operator_id = (
                case_row["assigned_to"]
                if (
                    case_row is not None
                    and case_row["assigned_to"] is not None
                )
                else None
            )

            record_case_event(
                case_id=task["case_id"],
                event_type="task_completed",
                actor_type=(
                    "human"
                    if operator_id is not None
                    else "system"
                ),
                actor_id=(
                    operator_id
                    if operator_id is not None
                    else "task_service"
                ),
                summary="Operational task completed.",
                metadata={
                    "task_id": task_id,
                    "category": task["category"],
                    "title": task["title"],
                },
                connection=connection,
            )

        connection.commit()

        updated_row = connection.execute(
            """
            SELECT *
            FROM tasks
            WHERE task_id = ?
            """,
            (task_id,),
        ).fetchone()

        return dict(updated_row)

    finally:
        connection.close()