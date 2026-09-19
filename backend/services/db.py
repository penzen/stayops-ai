import os
from pathlib import Path
import sqlite3


# Default database used by the normal StayOps application.
DEFAULT_DB_PATH = (
    Path(__file__).resolve().parents[1]
    / "database"
    / "stayops.db"
)


def get_db_path() -> Path:
    """
    Return the database StayOps should use.

    Normal application:
        backend/database/stayops.db

    Evaluations/tests can override this with:
        STAYOPS_DB_PATH
    """

    custom_path = os.getenv("STAYOPS_DB_PATH")

    if custom_path:
        return Path(custom_path).resolve()

    return DEFAULT_DB_PATH


def get_connection():
    db_path = get_db_path()

    connection = sqlite3.connect(db_path)

    # Return rows like dictionaries instead of tuples.
    connection.row_factory = sqlite3.Row

    # Enforce foreign keys.
    connection.execute("PRAGMA foreign_keys = ON;")

    return connection


"""
The row_factory part is useful because instead of getting:

("book_0014", "gst_2631", "prop_15")

we can turn a row into:

{
    "booking_id": "book_0014",
    "guest_id": "gst_2631",
    "property_id": "prop_15"
}

Much cleaner for tools and agents.

STAYOPS_DB_PATH lets evaluations use a separate disposable
database without modifying the normal StayOps demo database.
"""