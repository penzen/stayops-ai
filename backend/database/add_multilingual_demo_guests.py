from backend.services.db import get_connection
from backend.database.demo_dates import get_active_demo_window

DEMO_GUESTS = [
    {
        "guest_id": "gst_demo_en_001",
        "first_name": "Emma",
        "last_name": "Carter",
        "email": "emma.carter@example.com",
        "phone": "+44 7700 900123",
        "guest_lang": "en",
        "locale": "en_GB",
        "guest_geo": "United Kingdom",
    },
    {
        "guest_id": "gst_demo_de_001",
        "first_name": "Lukas",
        "last_name": "Weber",
        "email": "lukas.weber@example.com",
        "phone": "+49 151 12345678",
        "guest_lang": "de",
        "locale": "de_DE",
        "guest_geo": "Germany",
    },
]


DEMO_BOOKINGS = [
    {
        "booking_id": "book_demo_en_001",
        "guest_id": "gst_demo_en_001",
        "property_id": "prop_15",
        "nights": 2,
        "total_price": 420.0,
        "book_status": "confirmed",
        "source": "Direct",
        "assigned_to": "GRO_254",
    },
    {
        "booking_id": "book_demo_de_001",
        "guest_id": "gst_demo_de_001",
        "property_id": "prop_15",
        "nights": 2,
        "total_price": 390.0,
        "book_status": "confirmed",
        "source": "Direct",
        "assigned_to": "GRO_254",
    },
]


def property_exists(connection, property_id: str) -> bool:
    row = connection.execute(
        """
        SELECT property_id
        FROM properties
        WHERE property_id = ?
        """,
        (property_id,),
    ).fetchone()

    return row is not None


def upsert_guest(connection, guest: dict):
    connection.execute(
        """
        INSERT INTO guests (
            guest_id,
            first_name,
            last_name,
            email,
            phone,
            guest_lang,
            locale,
            guest_geo
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)

        ON CONFLICT(guest_id)
        DO UPDATE SET
            first_name = excluded.first_name,
            last_name = excluded.last_name,
            email = excluded.email,
            phone = excluded.phone,
            guest_lang = excluded.guest_lang,
            locale = excluded.locale,
            guest_geo = excluded.guest_geo
        """,
        (
            guest["guest_id"],
            guest["first_name"],
            guest["last_name"],
            guest["email"],
            guest["phone"],
            guest["guest_lang"],
            guest["locale"],
            guest["guest_geo"],
        ),
    )


def upsert_booking(connection, booking: dict):
    connection.execute(
        """
        INSERT INTO bookings (
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

        ON CONFLICT(booking_id)
        DO UPDATE SET
            guest_id = excluded.guest_id,
            property_id = excluded.property_id,
            check_in = excluded.check_in,
            check_out = excluded.check_out,
            nights = excluded.nights,
            total_price = excluded.total_price,
            book_status = excluded.book_status,
            source = excluded.source,
            assigned_to = excluded.assigned_to
        """,
        (
            booking["booking_id"],
            booking["guest_id"],
            booking["property_id"],
            booking["check_in"],
            booking["check_out"],
            booking["nights"],
            booking["total_price"],
            booking["book_status"],
            booking["source"],
            booking["assigned_to"],
        ),
    )


def main():
    connection = get_connection()

    try:
        # Make sure the properties we want to use
        # actually exist before inserting bookings.
        for booking in DEMO_BOOKINGS:
            property_id = booking["property_id"]

            if not property_exists(
                connection,
                property_id,
            ):
                raise ValueError(
                    f"Property does not exist: {property_id}"
                )

        for guest in DEMO_GUESTS:
            upsert_guest(
                connection,
                guest,
            )

        check_in, check_out = get_active_demo_window()

        for booking in DEMO_BOOKINGS:
            active_booking = {
                **booking,
                "check_in": check_in,
                "check_out": check_out,
            }

            upsert_booking(
                connection,
                active_booking,
            )


        connection.commit()

        print("\nMultilingual demo guests created.")
        print("=" * 60)

        rows = connection.execute(
            """
            SELECT
                b.booking_id,
                g.guest_id,
                g.first_name,
                g.last_name,
                g.guest_lang,
                g.locale,
                b.property_id,
                b.book_status
            FROM bookings AS b
            JOIN guests AS g
                ON g.guest_id = b.guest_id
            WHERE b.booking_id IN (
                'book_demo_current_001',
                'book_demo_en_001',
                'book_demo_de_001'
            )
            ORDER BY g.guest_lang
            """
        ).fetchall()

        for row in rows:
            print(
                dict(row)
            )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()