import uuid

from backend.domain.enums import CaseStatus, IssueCategory
from .db import get_connection


def find_existing_open_case(
    booking_id: str,
    property_id: str,
    category: str,
):
    category = category.strip().lower()

    try:
        category = IssueCategory(category).value
    except ValueError:
        raise ValueError(
            f"Invalid case category: {category}"
        )

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM cases
            WHERE booking_id = ?
              AND property_id = ?
              AND category = ?
              AND status = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (
                booking_id,
                property_id,
                category,
                CaseStatus.OPEN,
            ),
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()


def create_case(
    booking_id: str,
    property_id: str,
    category: str,
    summary: str | None = None,
):
    category = category.strip().lower()

    try:
        category = IssueCategory(category).value
    except ValueError:
        raise ValueError(
            f"Invalid case category: {category}"
        )

    connection = get_connection()

    try:
        booking = connection.execute(
            """
            SELECT booking_id, property_id
            FROM bookings
            WHERE booking_id = ?
            """,
            (booking_id,),
        ).fetchone()

        if booking is None:
            raise ValueError(
                f"Booking does not exist: {booking_id}"
            )

        if booking["property_id"] != property_id:
            raise ValueError(
                "Property does not belong to the supplied booking."
            )

        case_id = f"case_{uuid.uuid4().hex[:12]}"

        connection.execute(
            """
            INSERT INTO cases (
                case_id,
                booking_id,
                property_id,
                category,
                status,
                summary
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                case_id,
                booking_id,
                property_id,
                category,
                CaseStatus.OPEN,
                summary,
            ),
        )

        connection.commit()

        row = connection.execute(
            """
            SELECT *
            FROM cases
            WHERE case_id = ?
            """,
            (case_id,),
        ).fetchone()

        return dict(row)

    finally:
        connection.close()


def ensure_case(
    booking_id: str,
    property_id: str,
    category: str,
    summary: str | None = None,
):
    existing_case = find_existing_open_case(
        booking_id=booking_id,
        property_id=property_id,
        category=category,
    )

    if existing_case is not None:
        return {
            "created": False,
            "reason": "existing_open_case",
            "case": existing_case,
        }

    case = create_case(
        booking_id=booking_id,
        property_id=property_id,
        category=category,
        summary=summary,
    )

    return {
        "created": True,
        "reason": "case_created",
        "case": case,
    }

def get_case(case_id: str):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM cases
            WHERE case_id = ?
            """,
            (case_id,),
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()

def get_open_cases_for_booking(booking_id: str):
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM cases
            WHERE booking_id = ?
              AND status = ?
            ORDER BY created_at DESC
            """,
            (
                booking_id,
                CaseStatus.OPEN,
            ),
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()