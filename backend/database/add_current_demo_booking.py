import sqlite3
from pathlib import Path
from backend.database.demo_dates import get_active_demo_window

DB_PATH = Path("backend/database/stayops.db")


def add_demo_booking():

    check_in, check_out = get_active_demo_window()
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON;")

    try:
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

        connection.commit()

        print("Current demo booking added.")

    finally:
        connection.close()


if __name__ == "__main__":
    add_demo_booking()