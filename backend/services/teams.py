from .db import get_connection


def get_maintenance_workers():
    """
    Return workers who are eligible for operational
    maintenance task assignment.
    """

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT *
            FROM teams
            WHERE team_group = ?
            ORDER BY first_name ASC, last_name ASC
            """,
            ("technical_maintenance",),
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:
        connection.close()