import sqlite3


connection = sqlite3.connect("backend/database/stayops.db")

cursor = connection.cursor()

cursor.execute("""
    SELECT *
    FROM bookings
    WHERE book_status = 'confirmed'
    LIMIT 5
""")

rows = cursor.fetchall()

for row in rows:
    print(row)

connection.close()