from __future__ import annotations

import hashlib
import secrets
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone

from backend.database.demo_dates import get_active_demo_window
from backend.services.db import get_connection


DEMO_SESSION_TTL_HOURS = 6
MAX_CUSTOM_STAYS_PER_SESSION = 3

SAMPLE_BOOKING_IDS = (
    "book_demo_current_001",
    "book_demo_en_001",
    "book_demo_de_001",
)


class DemoSessionError(ValueError):
    """Base error for public demo session failures."""


class DemoSessionUnauthorized(DemoSessionError):
    pass


class DemoSessionExpired(DemoSessionError):
    pass


class DemoSessionAccessDenied(DemoSessionError):
    pass


class DemoSessionLimitExceeded(DemoSessionError):
    pass


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(
        microsecond=0
    )


def _db_timestamp(value: datetime) -> str:
    return value.astimezone(
        timezone.utc
    ).replace(
        tzinfo=None
    ).isoformat(
        sep=" "
    )


def _token_hash(token: str) -> str:
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def ensure_demo_session_schema(
    connection: sqlite3.Connection | None = None,
):
    owns_connection = connection is None

    if connection is None:
        connection = get_connection()

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS demo_sessions (
                session_id TEXT PRIMARY KEY,
                token_hash TEXT NOT NULL UNIQUE,
                created_at DATETIME NOT NULL,
                last_seen_at DATETIME NOT NULL,
                expires_at DATETIME NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS demo_session_bookings (
                session_id TEXT NOT NULL,
                booking_id VARCHAR(64) NOT NULL UNIQUE,
                resource_kind VARCHAR(32) NOT NULL,
                created_at DATETIME NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                PRIMARY KEY (
                    session_id,
                    booking_id
                ),

                FOREIGN KEY (session_id)
                    REFERENCES demo_sessions(session_id),

                FOREIGN KEY (booking_id)
                    REFERENCES bookings(booking_id)
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_demo_session_bookings_session
            ON demo_session_bookings(session_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_demo_sessions_expiry
            ON demo_sessions(expires_at)
            """
        )

        if owns_connection:
            connection.commit()

    finally:
        if owns_connection:
            connection.close()


def _session_row_by_id(
    connection: sqlite3.Connection,
    session_id: str,
):
    return connection.execute(
        """
        SELECT *
        FROM demo_sessions
        WHERE session_id = ?
        """,
        (session_id,),
    ).fetchone()


def _session_row_by_token(
    connection: sqlite3.Connection,
    token: str,
):
    return connection.execute(
        """
        SELECT *
        FROM demo_sessions
        WHERE token_hash = ?
        """,
        (_token_hash(token),),
    ).fetchone()


def _assert_session_active_row(
    row,
):
    if row is None:
        raise DemoSessionUnauthorized(
            "Demo session is invalid."
        )

    expires_at = datetime.fromisoformat(
        row["expires_at"]
    ).replace(
        tzinfo=timezone.utc
    )

    if expires_at <= _utc_now():
        raise DemoSessionExpired(
            "Demo session has expired."
        )


def validate_demo_session(
    token: str,
):
    if not token or not token.strip():
        raise DemoSessionUnauthorized(
            "Demo session token is required."
        )

    connection = get_connection()

    try:
        ensure_demo_session_schema(
            connection
        )

        row = _session_row_by_token(
            connection,
            token.strip(),
        )

        _assert_session_active_row(row)

        now = _db_timestamp(
            _utc_now()
        )

        connection.execute(
            """
            UPDATE demo_sessions
            SET last_seen_at = ?
            WHERE session_id = ?
            """,
            (
                now,
                row["session_id"],
            ),
        )
        connection.commit()

        refreshed = _session_row_by_id(
            connection,
            row["session_id"],
        )

        return dict(refreshed)

    finally:
        connection.close()


def assert_demo_session_exists(
    session_id: str,
    *,
    connection: sqlite3.Connection | None = None,
):
    owns_connection = connection is None

    if connection is None:
        connection = get_connection()

    try:
        ensure_demo_session_schema(
            connection
        )

        row = _session_row_by_id(
            connection,
            session_id,
        )

        _assert_session_active_row(row)

        return dict(row)

    finally:
        if owns_connection:
            connection.close()


def register_demo_booking(
    *,
    session_id: str,
    booking_id: str,
    resource_kind: str,
    connection: sqlite3.Connection | None = None,
):
    owns_connection = connection is None

    if connection is None:
        connection = get_connection()

    try:
        assert_demo_session_exists(
            session_id,
            connection=connection,
        )

        connection.execute(
            """
            INSERT INTO demo_session_bookings (
                session_id,
                booking_id,
                resource_kind
            )
            VALUES (?, ?, ?)
            """,
            (
                session_id,
                booking_id,
                resource_kind,
            ),
        )

        if owns_connection:
            connection.commit()

    finally:
        if owns_connection:
            connection.close()


def count_custom_demo_stays(
    session_id: str,
    *,
    connection: sqlite3.Connection | None = None,
) -> int:
    owns_connection = connection is None

    if connection is None:
        connection = get_connection()

    try:
        ensure_demo_session_schema(
            connection
        )

        row = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM demo_session_bookings
            WHERE session_id = ?
              AND resource_kind = 'custom'
            """,
            (session_id,),
        ).fetchone()

        return int(row["count"])

    finally:
        if owns_connection:
            connection.close()


def require_demo_booking_access(
    *,
    session_id: str,
    booking_id: str,
):
    connection = get_connection()

    try:
        ensure_demo_session_schema(
            connection
        )

        row = connection.execute(
            """
            SELECT 1
            FROM demo_session_bookings
            WHERE session_id = ?
              AND booking_id = ?
            """,
            (
                session_id,
                booking_id,
            ),
        ).fetchone()

        if row is None:
            raise DemoSessionAccessDenied(
                "Booking does not belong to this demo session."
            )

    finally:
        connection.close()


def get_demo_session_booking_ids(
    session_id: str,
):
    connection = get_connection()

    try:
        ensure_demo_session_schema(
            connection
        )

        rows = connection.execute(
            """
            SELECT booking_id
            FROM demo_session_bookings
            WHERE session_id = ?
            ORDER BY created_at, booking_id
            """,
            (session_id,),
        ).fetchall()

        return [
            row["booking_id"]
            for row in rows
        ]

    finally:
        connection.close()


def get_demo_session_stays(
    session_id: str,
):
    connection = get_connection()

    try:
        ensure_demo_session_schema(
            connection
        )

        rows = connection.execute(
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

                p.title AS property_title,

                dsb.resource_kind

            FROM demo_session_bookings AS dsb

            JOIN bookings AS b
                ON b.booking_id = dsb.booking_id

            JOIN guests AS g
                ON g.guest_id = b.guest_id

            JOIN properties AS p
                ON p.property_id = b.property_id

            WHERE dsb.session_id = ?

            ORDER BY
                CASE dsb.resource_kind
                    WHEN 'custom' THEN 0
                    ELSE 1
                END,
                dsb.created_at DESC,
                g.first_name,
                g.last_name
            """,
            (session_id,),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()


def _clone_sample_stays(
    *,
    connection: sqlite3.Connection,
    session_id: str,
):
    check_in, check_out = (
        get_active_demo_window()
    )

    session_suffix = (
        session_id
        .replace("dms_", "")[:10]
    )

    for index, source_booking_id in enumerate(
        SAMPLE_BOOKING_IDS,
        start=1,
    ):
        row = connection.execute(
            """
            SELECT
                b.*,
                g.first_name,
                g.last_name,
                g.email,
                g.phone,
                g.guest_lang,
                g.locale,
                g.guest_geo
            FROM bookings AS b
            JOIN guests AS g
                ON g.guest_id = b.guest_id
            WHERE b.booking_id = ?
            """,
            (source_booking_id,),
        ).fetchone()

        if row is None:
            raise DemoSessionError(
                "A seeded demo stay is missing."
            )

        guest_id = (
            f"gst_demo_session_"
            f"{session_suffix}_{index}"
        )
        booking_id = (
            f"book_demo_session_"
            f"{session_suffix}_{index}"
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
                row["first_name"],
                row["last_name"],
                row["email"],
                row["phone"],
                row["guest_lang"],
                row["locale"],
                row["guest_geo"],
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
                row["property_id"],
                check_in,
                check_out,
                row["nights"],
                row["total_price"],
                "confirmed",
                "StayOps Demo Session",
                row["assigned_to"],
            ),
        )

        register_demo_booking(
            session_id=session_id,
            booking_id=booking_id,
            resource_kind="sample",
            connection=connection,
        )


def create_demo_session():
    cleanup_expired_demo_sessions()

    connection = get_connection()

    try:
        ensure_demo_session_schema(
            connection
        )

        session_id = (
            f"dms_{uuid.uuid4().hex[:16]}"
        )
        token = secrets.token_urlsafe(32)

        now = _utc_now()
        expires_at = (
            now
            + timedelta(
                hours=DEMO_SESSION_TTL_HOURS
            )
        )

        connection.execute(
            """
            INSERT INTO demo_sessions (
                session_id,
                token_hash,
                created_at,
                last_seen_at,
                expires_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session_id,
                _token_hash(token),
                _db_timestamp(now),
                _db_timestamp(now),
                _db_timestamp(expires_at),
            ),
        )

        _clone_sample_stays(
            connection=connection,
            session_id=session_id,
        )

        connection.commit()

        return {
            "session_id": session_id,
            "session_token": token,
            "expires_at": (
                _db_timestamp(expires_at)
            ),
            "ttl_hours": (
                DEMO_SESSION_TTL_HOURS
            ),
            "sample_stays": (
                get_demo_session_stays(
                    session_id
                )
            ),
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def _cleanup_session_with_connection(
    *,
    connection: sqlite3.Connection,
    session_id: str,
):
    rows = connection.execute(
        """
        SELECT
            dsb.booking_id,
            b.guest_id
        FROM demo_session_bookings AS dsb
        JOIN bookings AS b
            ON b.booking_id = dsb.booking_id
        WHERE dsb.session_id = ?
        """,
        (session_id,),
    ).fetchall()

    booking_ids = [
        row["booking_id"]
        for row in rows
    ]
    guest_ids = {
        row["guest_id"]
        for row in rows
    }

    for booking_id in booking_ids:
        connection.execute(
            """
            DELETE FROM compensation_decisions
            WHERE compensation_request_id IN (
                SELECT compensation_request_id
                FROM compensation_requests
                WHERE booking_id = ?
            )
            """,
            (booking_id,),
        )

        connection.execute(
            """
            DELETE FROM compensation_requests
            WHERE booking_id = ?
            """,
            (booking_id,),
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
            (booking_id,),
        )

        connection.execute(
            """
            DELETE FROM escalations
            WHERE booking_id = ?
            """,
            (booking_id,),
        )

        connection.execute(
            """
            DELETE FROM tasks
            WHERE booking_id = ?
            """,
            (booking_id,),
        )

        connection.execute(
            """
            DELETE FROM messages
            WHERE booking_id = ?
            """,
            (booking_id,),
        )

        connection.execute(
            """
            DELETE FROM incidents
            WHERE booking_id = ?
            """,
            (booking_id,),
        )

        connection.execute(
            """
            DELETE FROM cases
            WHERE booking_id = ?
            """,
            (booking_id,),
        )

    connection.execute(
        """
        DELETE FROM demo_session_bookings
        WHERE session_id = ?
        """,
        (session_id,),
    )

    for booking_id in booking_ids:
        connection.execute(
            """
            DELETE FROM bookings
            WHERE booking_id = ?
            """,
            (booking_id,),
        )

    for guest_id in guest_ids:
        connection.execute(
            """
            DELETE FROM guests
            WHERE guest_id = ?
              AND NOT EXISTS (
                  SELECT 1
                  FROM bookings
                  WHERE bookings.guest_id = guests.guest_id
              )
            """,
            (guest_id,),
        )

    connection.execute(
        """
        DELETE FROM demo_sessions
        WHERE session_id = ?
        """,
        (session_id,),
    )

    return len(booking_ids)


def delete_demo_session(
    session_id: str,
):
    connection = get_connection()

    try:
        ensure_demo_session_schema(
            connection
        )

        deleted_bookings = (
            _cleanup_session_with_connection(
                connection=connection,
                session_id=session_id,
            )
        )

        connection.commit()

        return {
            "session_id": session_id,
            "status": "deleted",
            "deleted_bookings": (
                deleted_bookings
            ),
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def cleanup_expired_demo_sessions():
    connection = get_connection()

    try:
        ensure_demo_session_schema(
            connection
        )

        now = _db_timestamp(
            _utc_now()
        )

        rows = connection.execute(
            """
            SELECT session_id
            FROM demo_sessions
            WHERE expires_at <= ?
            """,
            (now,),
        ).fetchall()

        deleted_sessions = 0
        deleted_bookings = 0

        for row in rows:
            deleted_bookings += (
                _cleanup_session_with_connection(
                    connection=connection,
                    session_id=row["session_id"],
                )
            )
            deleted_sessions += 1

        connection.commit()

        return {
            "deleted_sessions": (
                deleted_sessions
            ),
            "deleted_bookings": (
                deleted_bookings
            ),
        }

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

def _require_session_booking_row(
    connection: sqlite3.Connection,
    *,
    session_id: str,
    booking_id: str,
):
    row = connection.execute(
        """
        SELECT 1
        FROM demo_session_bookings
        WHERE session_id = ?
          AND booking_id = ?
        """,
        (session_id, booking_id),
    ).fetchone()

    if row is None:
        raise DemoSessionAccessDenied(
            "Resource does not belong to this demo session."
        )


def require_demo_guest_access(
    *,
    session_id: str,
    guest_id: str,
):
    connection = get_connection()

    try:
        ensure_demo_session_schema(connection)

        row = connection.execute(
            """
            SELECT b.booking_id
            FROM bookings AS b
            JOIN demo_session_bookings AS dsb
              ON dsb.booking_id = b.booking_id
            WHERE dsb.session_id = ?
              AND b.guest_id = ?
            LIMIT 1
            """,
            (session_id, guest_id),
        ).fetchone()

        if row is None:
            raise DemoSessionAccessDenied(
                "Guest does not belong to this demo session."
            )

    finally:
        connection.close()


def _require_resource_access(
    *,
    session_id: str,
    query: str,
    resource_id: str,
    label: str,
):
    connection = get_connection()

    try:
        ensure_demo_session_schema(connection)

        row = connection.execute(
            query,
            (resource_id,),
        ).fetchone()

        if row is None:
            raise DemoSessionAccessDenied(
                f"{label} does not belong to this demo session."
            )

        _require_session_booking_row(
            connection,
            session_id=session_id,
            booking_id=row["booking_id"],
        )

    finally:
        connection.close()


def require_demo_case_access(*, session_id: str, case_id: str):
    _require_resource_access(
        session_id=session_id,
        query="SELECT booking_id FROM cases WHERE case_id = ?",
        resource_id=case_id,
        label="Case",
    )


def require_demo_task_access(*, session_id: str, task_id: str):
    _require_resource_access(
        session_id=session_id,
        query="SELECT booking_id FROM tasks WHERE task_id = ?",
        resource_id=task_id,
        label="Task",
    )


def require_demo_escalation_access(*, session_id: str, escalation_id: str):
    _require_resource_access(
        session_id=session_id,
        query="SELECT booking_id FROM escalations WHERE escalation_id = ?",
        resource_id=escalation_id,
        label="Escalation",
    )


def require_demo_compensation_access(*, session_id: str, compensation_request_id: str):
    _require_resource_access(
        session_id=session_id,
        query=(
            "SELECT booking_id FROM compensation_requests "
            "WHERE compensation_request_id = ?"
        ),
        resource_id=compensation_request_id,
        label="Compensation request",
    )


def require_demo_incident_access(*, session_id: str, incident_id: str):
    _require_resource_access(
        session_id=session_id,
        query="SELECT booking_id FROM incidents WHERE incident_id = ?",
        resource_id=incident_id,
        label="Incident",
    )

