import re
import uuid

from backend.database.demo_dates import get_active_demo_window
from backend.services.db import get_connection


LANGUAGE_DEFAULTS = {
    "en": {
        "locale": "en_GB",
        "guest_geo": "Demo guest",
    },
    "de": {
        "locale": "de_DE",
        "guest_geo": "Demo guest",
    },
    "fr": {
        "locale": "fr_FR",
        "guest_geo": "Demo guest",
    },
}


def get_demo_properties():
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                property_id,
                title,
                city,
                max_guests,
                base_price,
                cleaning_fee
            FROM properties
            ORDER BY city, title
            """
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


def _clean_name(value: str, field_name: str) -> str:
    cleaned = value.strip()

    if not cleaned:
        raise ValueError(f"{field_name} is required.")

    if len(cleaned) > 80:
        raise ValueError(f"{field_name} is too long.")

    return cleaned


def _demo_email(
    email: str | None,
    first_name: str,
    last_name: str,
) -> str:
    if email is not None:
        cleaned = email.strip().lower()

        if cleaned:
            if "@" not in cleaned or len(cleaned) > 255:
                raise ValueError(
                    "Enter a valid email address."
                )

            return cleaned

    slug = re.sub(
        r"[^a-z0-9]+",
        ".",
        f"{first_name}.{last_name}".lower(),
    ).strip(".")

    suffix = uuid.uuid4().hex[:8]

    return (
        f"{slug or 'guest'}.{suffix}"
        "@stayops-demo.example"
    )


def create_demo_guest_stay(
    *,
    first_name: str,
    last_name: str,
    property_id: str,
    guest_lang: str = "en",
    email: str | None = None,
):
    first_name = _clean_name(
        first_name,
        "First name",
    )
    last_name = _clean_name(
        last_name,
        "Last name",
    )

    property_id = property_id.strip()

    if not property_id:
        raise ValueError("Property is required.")

    normalized_language = (
        guest_lang.strip().lower()
    )

    language_defaults = LANGUAGE_DEFAULTS.get(
        normalized_language
    )

    if language_defaults is None:
        raise ValueError(
            "Unsupported demo language."
        )

    normalized_email = _demo_email(
        email,
        first_name,
        last_name,
    )

    connection = get_connection()

    try:
        property_row = connection.execute(
            """
            SELECT
                property_id,
                title,
                base_price,
                cleaning_fee
            FROM properties
            WHERE property_id = ?
            """,
            (property_id,),
        ).fetchone()

        if property_row is None:
            raise ValueError(
                "Selected property does not exist."
            )

        guest_id = (
            "gst_demo_custom_"
            f"{uuid.uuid4().hex[:12]}"
        )
        booking_id = (
            "book_demo_custom_"
            f"{uuid.uuid4().hex[:12]}"
        )

        check_in, check_out = (
            get_active_demo_window()
        )

        nights = 2

        base_price = float(
            property_row["base_price"] or 0
        )
        cleaning_fee = float(
            property_row["cleaning_fee"] or 0
        )

        total_price = round(
            (base_price * nights)
            + cleaning_fee,
            2,
        )

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
            """,
            (
                guest_id,
                first_name,
                last_name,
                normalized_email,
                None,
                normalized_language,
                language_defaults["locale"],
                language_defaults["guest_geo"],
            ),
        )

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
            """,
            (
                booking_id,
                guest_id,
                property_id,
                check_in,
                check_out,
                nights,
                total_price,
                "confirmed",
                "StayOps Demo",
                "GRO_254",
            ),
        )

        connection.commit()

        row = connection.execute(
            """
            SELECT
                b.booking_id,
                b.guest_id,
                b.property_id,
                b.check_in,
                b.check_out,
                b.book_status,
                b.nights,
                b.total_price,
                g.first_name,
                g.last_name,
                g.email,
                g.guest_lang,
                g.locale,
                p.title AS property_title
            FROM bookings AS b
            JOIN guests AS g
                ON g.guest_id = b.guest_id
            JOIN properties AS p
                ON p.property_id = b.property_id
            WHERE b.booking_id = ?
            """,
            (booking_id,),
        ).fetchone()

        return dict(row)

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
