from backend.services.db import get_connection


def main():
    with get_connection() as connection:
        cursor = connection.cursor()

        # Check whether the column already exists
        cursor.execute("PRAGMA table_info(escalations)")
        columns = [row["name"] for row in cursor.fetchall()]

        if "category" not in columns:
            cursor.execute(
                """
                ALTER TABLE escalations
                ADD COLUMN category TEXT NOT NULL DEFAULT 'other'
                """
            )

            print("Added category column to escalations.")
        else:
            print("category column already exists.")

        # Backfill escalation categories from incidents where possible
        cursor.execute(
            """
            UPDATE escalations
            SET category = (
                SELECT incidents.category
                FROM incidents
                WHERE incidents.incident_id = escalations.incident_id
            )
            WHERE incident_id IS NOT NULL
            AND EXISTS (
                SELECT 1
                FROM incidents
                WHERE incidents.incident_id = escalations.incident_id
            )
            """
        )

        # We know this existing escalation is the lockout/access escalation
        cursor.execute(
            """
            UPDATE escalations
            SET category = 'access'
            WHERE escalation_id = 'esc_7fc12afbb5c0'
            """
        )

        connection.commit()

        cursor.execute(
            """
            SELECT
                escalation_id,
                booking_id,
                property_id,
                category,
                reason,
                status
            FROM escalations
            ORDER BY created_at
            """
        )

        print("\nESCALATIONS")
        print("=" * 80)

        for row in cursor.fetchall():
            print(dict(row))


if __name__ == "__main__":
    main()