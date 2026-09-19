from .db import get_connection


def get_property(property_id: str):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM properties
            WHERE property_id = ?
            """,
            (property_id,),
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()


def get_access_system(property_id: str):
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT *
            FROM access_systems
            WHERE property_id = ?
            """,
            (property_id,),
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:
        connection.close()