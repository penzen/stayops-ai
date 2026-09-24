import argparse
import sqlite3
from pathlib import Path
from backend.database.demo_dates import get_active_demo_window

from backend.database.add_stayops_tables import (
    create_tables,
    add_case_links,
    create_indexes,
    seed_access_systems,
    seed_demo_scenario,
)
from backend.database.add_multilingual_demo_guests import (
    DEMO_GUESTS,
    DEMO_BOOKINGS,
    property_exists,
    upsert_guest,
    upsert_booking,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SOURCE_SQL = (
    PROJECT_ROOT
    / "data"
    / "pandoxyd"
    / "database_setup_demo.sql"
)

DEFAULT_DB_PATH = (
    PROJECT_ROOT
    / "backend"
    / "database"
    / "stayops.db"
)


def seed_current_demo_booking(connection: sqlite3.Connection):
    check_in, check_out = get_active_demo_window()

    connection.execute(
        """
        INSERT OR IGNORE INTO bookings (
            booking_id,
            guest_id,
            property_id,
            check_in,
            check_out,
            nights,
            total_price,
            book_status,
            source,
            assigned_to
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "book_demo_current_001",
            "gst_2631",
            "prop_15",
            check_in,
            check_out,
            2,
            978.00,
            "confirmed",
            "Direct",
            "GRO_254",
        ),
    )


def seed_multilingual_demo_data(connection: sqlite3.Connection):
    for booking in DEMO_BOOKINGS:
        if not property_exists(
            connection,
            booking["property_id"],
        ):
            raise ValueError(
                f"Property does not exist: {booking['property_id']}"
            )

    for guest in DEMO_GUESTS:
        upsert_guest(connection, guest)

    check_in, check_out = get_active_demo_window()

    for booking in DEMO_BOOKINGS:
        active_booking = {
            **booking,
            "check_in": check_in,
            "check_out": check_out,
        }

        upsert_booking(connection, active_booking)


def print_summary(connection: sqlite3.Connection):
    tables = [
        "properties",
        "guests",
        "teams",
        "bookings",
        "cases",
        "tasks",
        "access_systems",
        "messages",
        "incidents",
        "escalations",
    ]

    print("\nDATABASE SUMMARY")
    print("=" * 50)

    for table in tables:
        count = connection.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]

        print(f"{table:<20} {count}")


def bootstrap_database(
    db_path: Path,
    force: bool = False,
):
    if not SOURCE_SQL.exists():
        raise FileNotFoundError(
            f"Base SQL file not found: {SOURCE_SQL}"
        )

    if db_path.exists():
        if not force:
            raise FileExistsError(
                f"Database already exists: {db_path}\n"
                "Use --force if you intentionally want to rebuild it."
            )

        db_path.unlink()

    db_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON;")

    try:
        print(f"Creating database: {db_path}")

        base_sql = SOURCE_SQL.read_text(
            encoding="utf-8"
        )

        # 1. Create the original STR-Ops dataset.
        connection.executescript(base_sql)

        # 2. Add StayOps-specific schema.
        create_tables(connection)
        add_case_links(connection)
        create_indexes(connection)

        # 3. Seed StayOps operational data.
        seed_access_systems(connection)
        seed_demo_scenario(connection)

        # 4. Add demo bookings and guests.
        seed_current_demo_booking(connection)
        seed_multilingual_demo_data(connection)

        connection.commit()

        print_summary(connection)

        print("\nStayOps database bootstrap complete.")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser(
        description="Build a fresh StayOps SQLite database."
    )

    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_DB_PATH,
        help="Path for the generated SQLite database.",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace the database if it already exists.",
    )

    args = parser.parse_args()

    bootstrap_database(
        db_path=args.db_path,
        force=args.force,
    )


if __name__ == "__main__":
    main()



"""
database_setup_demo.sql
          ↓
   bootstrap.py
          ↓
 original tables/data
          ↓
 StayOps tables/indexes
          ↓
 access systems
          ↓
 demo operational data
          ↓
 multilingual demo data
          ↓
     stayops.db

"""