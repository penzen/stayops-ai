import json
import uuid

from .db import get_connection


def _format_case_event(row):
    event = dict(row)

    metadata_json = event.pop(
        "metadata_json"
    )

    if metadata_json:
        event["metadata"] = json.loads(
            metadata_json
        )
    else:
        event["metadata"] = {}

    return event


def record_case_event(
    case_id: str,
    event_type: str,
    actor_type: str,
    summary: str,
    actor_id: str | None = None,
    metadata: dict | None = None,
    connection=None,
):
    """
    Append one operationally meaningful event to a Case.

    When a database connection is supplied, the caller owns
    the transaction. This allows Case state changes and their
    audit events to commit atomically.

    When no connection is supplied, this function manages
    its own transaction.
    """

    event_type = event_type.strip()
    actor_type = actor_type.strip()
    summary = summary.strip()

    if not event_type:
        raise ValueError(
            "event_type is required."
        )

    if not actor_type:
        raise ValueError(
            "actor_type is required."
        )

    if not summary:
        raise ValueError(
            "summary is required."
        )

    owns_connection = connection is None

    if owns_connection:
        connection = get_connection()

    try:
        case_row = connection.execute(
            """
            SELECT case_id
            FROM cases
            WHERE case_id = ?
            """,
            (case_id,),
        ).fetchone()

        if case_row is None:
            raise ValueError(
                f"Case does not exist: {case_id}"
            )

        case_event_id = (
            "evt_"
            + uuid.uuid4().hex[:12]
        )

        metadata_json = json.dumps(
            metadata or {},
            ensure_ascii=False,
            sort_keys=True,
        )

        connection.execute(
            """
            INSERT INTO case_events (
                case_event_id,
                case_id,
                event_type,
                actor_type,
                actor_id,
                summary,
                metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                case_event_id,
                case_id,
                event_type,
                actor_type,
                actor_id,
                summary,
                metadata_json,
            ),
        )

        if owns_connection:
            connection.commit()

        row = connection.execute(
            """
            SELECT *
            FROM case_events
            WHERE case_event_id = ?
            """,
            (case_event_id,),
        ).fetchone()

        return _format_case_event(
            row
        )

    except Exception:
        if owns_connection:
            connection.rollback()

        raise

    finally:
        if owns_connection:
            connection.close()


def get_case_timeline(
    case_id: str,
):
    """
    Return the operational audit timeline for one Case
    in chronological order.
    """

    connection = get_connection()

    try:
        case_row = connection.execute(
            """
            SELECT case_id
            FROM cases
            WHERE case_id = ?
            """,
            (case_id,),
        ).fetchone()

        if case_row is None:
            raise ValueError(
                f"Case does not exist: {case_id}"
            )

        rows = connection.execute(
            """
            SELECT *
            FROM case_events
            WHERE case_id = ?
            ORDER BY
                created_at ASC,
                rowid ASC
            """,
            (case_id,),
        ).fetchall()

        return [
            _format_case_event(row)
            for row in rows
        ]

    finally:
        connection.close()