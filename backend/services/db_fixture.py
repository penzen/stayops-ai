import shutil
import sqlite3
from pathlib import Path

from backend.database.add_stayops_tables import (
    create_tables,
    add_case_links,
    create_indexes,
    add_case_handoff_fields,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SOURCE_DB = (
    PROJECT_ROOT
    / "backend"
    / "database"
    / "stayops.db"
)

EVAL_DB = (
    PROJECT_ROOT
    / "backend"
    / "database"
    / "stayops_eval.db"
)


DEMO_BOOKING_ID = "book_demo_current_001"

def reset_eval_database() -> Path:
    """
    Create a fresh evaluation database from the normal StayOps
    database and remove mutable operational state associated with
    the demo booking.

    Static data remains:
    - guests
    - bookings
    - properties
    - teams
    - access systems

    Scenario-generated state is cleared:
    - messages
    - tasks
    - incidents
    - escalations
    - compensation decisions
    - compensation requests
    - cases
    - case events
    """

    if not SOURCE_DB.exists():
        raise FileNotFoundError(
            f"Source database not found:\n{SOURCE_DB}"
        )

    if EVAL_DB.exists():
        EVAL_DB.unlink()

    shutil.copy2(
        SOURCE_DB,
        EVAL_DB,
    )

    connection = sqlite3.connect(EVAL_DB)

    connection.execute(
        "PRAGMA foreign_keys = ON;"
    )
    

    try:

        # Ensure the copied evaluation database uses
        # the current StayOps schema.
        create_tables(connection)
        add_case_links(connection)
        add_case_handoff_fields(connection)
        create_indexes(connection)
        
        # Delete dependent operational records first.
        connection.execute(
            """
            DELETE FROM escalations
            WHERE booking_id = ?
            """,
            (DEMO_BOOKING_ID,),
        )

        connection.execute(
            """
            DELETE FROM tasks
            WHERE booking_id = ?
            """,
            (DEMO_BOOKING_ID,),
        )

        connection.execute(
            """
            DELETE FROM messages
            WHERE booking_id = ?
            """,
            (DEMO_BOOKING_ID,),
        )

        connection.execute(
            """
            DELETE FROM incidents
            WHERE booking_id = ?
            """,
            (DEMO_BOOKING_ID,),
        )

        # Cases must be deleted after tasks and escalations
        # because those records may reference a Case.

        connection.execute(
            """
            DELETE FROM compensation_decisions
            WHERE compensation_request_id IN (
                SELECT compensation_request_id
                FROM compensation_requests
                WHERE booking_id = ?
            )
            """,
            (DEMO_BOOKING_ID,),
        )

        connection.execute(
            """
            DELETE FROM compensation_requests
            WHERE booking_id = ?
            """,
            (DEMO_BOOKING_ID,),
        )
        connection.execute(
            """
            DELETE FROM case_events
            WHERE case_id IN (
                SELECT case_id
                FROM cases
                WHERE booking_id = ?
            )
            """,
            (DEMO_BOOKING_ID,),
        )
        connection.execute(
            """
            DELETE FROM cases
            WHERE booking_id = ?
            """,
            (DEMO_BOOKING_ID,),
        )

        connection.commit()

    finally:
        connection.close()

    return EVAL_DB