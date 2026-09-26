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

def complete_task(task_id: str,operator_id: str | None = None,):
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

            if task["case_id"] is None:
                raise ValueError(
                    "Task must belong to a Case "
                    "before human completion."
                )

            case_row = connection.execute(
                """
                SELECT *
                FROM cases
                WHERE case_id = ?
                """,
                (task["case_id"],),
            ).fetchone()

            if case_row is None:
                raise ValueError(
                    f"Case does not exist: {task['case_id']}"
                )

            case = dict(case_row)

            if case["status"] != "waiting_human":
                raise ValueError(
                    "Case must be waiting_human "
                    "before human task completion."
                )

            if case["assigned_to"] is None:
                raise ValueError(
                    "Case must be claimed before "
                    "completing human operational work."
                )

            if case["assigned_to"] != operator_id:
                raise ValueError(
                    "Only the assigned Case operator "
                    "can complete this task."
                )

            authorized_operator_id = operator_id

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
            record_case_event(
                case_id=task["case_id"],
                event_type="task_completed",
                actor_type=(
                    "human"
                    if authorized_operator_id is not None
                    else "system"
                ),
                actor_id=(
                    authorized_operator_id
                    if authorized_operator_id is not None
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

def assign_task(
    task_id: str,
    operator_id: str,
    worker_id: str,
):
    """
    Assign an open Case-linked task to a maintenance worker.

    The Case must already be claimed by the operator making
    the assignment.
    """

    operator_id = operator_id.strip()
    worker_id = worker_id.strip()

    if not operator_id:
        raise ValueError(
            "Operator ID is required."
        )

    if not worker_id:
        raise ValueError(
            "Worker ID is required."
        )

    connection = get_connection()

    try:
        # -----------------------------------------------------
        # TASK
        # -----------------------------------------------------

        task_row = connection.execute(
            """
            SELECT *
            FROM tasks
            WHERE task_id = ?
            """,
            (task_id,),
        ).fetchone()

        if task_row is None:
            raise ValueError(
                f"Task does not exist: {task_id}"
            )

        task = dict(task_row)

        if task["task_status"] != "open":
            raise ValueError(
                "Only open tasks can be assigned."
            )

        if task["case_id"] is None:
            raise ValueError(
                "Task must belong to a Case before assignment."
            )

        # -----------------------------------------------------
        # CASE OWNERSHIP
        # -----------------------------------------------------

        case_row = connection.execute(
            """
            SELECT *
            FROM cases
            WHERE case_id = ?
            """,
            (task["case_id"],),
        ).fetchone()

        if case_row is None:
            raise ValueError(
                f"Case does not exist: {task['case_id']}"
            )

        case = dict(case_row)

        if case["status"] != "waiting_human":
            raise ValueError(
                "Case must be waiting_human "
                "before task assignment."
            )

        if case["assigned_to"] is None:
            raise ValueError(
                "Case must be claimed before "
                "assigning operational work."
            )

        if case["assigned_to"] != operator_id:
            raise ValueError(
                "Only the assigned Case operator "
                "can assign this task."
            )

        # -----------------------------------------------------
        # WORKER
        # -----------------------------------------------------

        worker_row = connection.execute(
            """
            SELECT *
            FROM teams
            WHERE team_id = ?
            """,
            (worker_id,),
        ).fetchone()

        if worker_row is None:
            raise ValueError(
                f"Worker does not exist: {worker_id}"
            )

        worker = dict(worker_row)

        if (
            worker["team_group"]
            != "technical_maintenance"
        ):
            raise ValueError(
                "Task worker must belong to "
                "technical_maintenance."
            )

        # -----------------------------------------------------
        # IDEMPOTENT REASSIGNMENT
        # -----------------------------------------------------

        if task["assigned_to"] == worker_id:
            return {
                "assigned": False,
                "reason": "already_assigned_to_worker",
                "task": task,
                "worker": worker,
            }

        previous_assignee = task["assigned_to"]

        # -----------------------------------------------------
        # ASSIGN
        # -----------------------------------------------------

        connection.execute(
            """
            UPDATE tasks
            SET assigned_to = ?
            WHERE task_id = ?
            """,
            (
                worker_id,
                task_id,
            ),
        )

        record_case_event(
            case_id=task["case_id"],
            event_type="task_assigned",
            actor_type="human",
            actor_id=operator_id,
            summary=(
                f"Operational task assigned to "
                f"{worker['first_name']} "
                f"{worker['last_name']}."
            ),
            metadata={
                "task_id": task_id,
                "worker_id": worker_id,
                "previous_assignee":
                    previous_assignee,
                "category": task["category"],
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

        return {
            "assigned": True,
            "reason": "task_assigned",
            "task": dict(updated_row),
            "worker": worker,
        }

    finally:
        connection.close()