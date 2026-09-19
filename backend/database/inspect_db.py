import sqlite3

DB_PATH = "backend/database/stayops.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

# Get all tables
cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    ORDER BY name;
""")

tables = [row[0] for row in cursor.fetchall()]

print("\nTABLES")
print("=" * 50)

for table in tables:
    print(f"\n{table.upper()}")
    print("-" * 50)

    cursor.execute(f"PRAGMA table_info({table})")

    columns = cursor.fetchall()

    for column in columns:
        column_id, name, data_type, not_null, default, primary_key = column

        print(
            f"{name:<25} "
            f"{data_type:<15} "
            f"PK={bool(primary_key)}"
        )

    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]

    print(f"\nRows: {count}")

connection.close()

"""
GUESTS
  ↓
BOOKINGS
  ↓
PROPERTIES
  ↓
TASKS
  ↓
TEAMS

"""


"""
Who sent this?
      ↓
gst_2631

Which reservation?
      ↓
book_0014

Which property?
      ↓
prop_15

Are there already open tasks?
      ↓
tasks table

Who is responsible?
      ↓
teams table
"""