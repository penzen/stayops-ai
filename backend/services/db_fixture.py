import shutil
import sqlite3
from pathlib import Path


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
    - cases
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
            DELETE FROM cases
            WHERE booking_id = ?
            """,
            (DEMO_BOOKING_ID,),
        )

        connection.commit()

    finally:
        connection.close()

    return EVAL_DB