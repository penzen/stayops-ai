from pathlib import Path
import sqlite3


DB_PATH = Path("backend/database/stayops.db")


def create_tables(connection: sqlite3.Connection):
    cursor = connection.cursor()

    # ---------------------------------------------------------
    # ACCESS SYSTEMS
    # One property can have an access/lock configuration.
    # ---------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS access_systems (
            access_id TEXT PRIMARY KEY,
            property_id VARCHAR(64) NOT NULL,

            access_type VARCHAR(100) NOT NULL,
            provider VARCHAR(100),
            lock_id VARCHAR(100),

            backup_method VARCHAR(255),

            agent_can_reset INTEGER NOT NULL DEFAULT 0,
            guest_verification_required INTEGER NOT NULL DEFAULT 1,

            status VARCHAR(50) NOT NULL DEFAULT 'online',

            FOREIGN KEY (property_id)
                REFERENCES properties(property_id)
        );
    """)

    # ---------------------------------------------------------
    # MESSAGES
    # Guest / agent / human operator conversation history.
    # ---------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            message_id TEXT PRIMARY KEY,

            booking_id VARCHAR(64),
            guest_id VARCHAR(64),

            sender_type VARCHAR(50) NOT NULL,
            message_text TEXT NOT NULL,

            channel VARCHAR(50) NOT NULL DEFAULT 'chat',

            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (booking_id)
                REFERENCES bookings(booking_id),

            FOREIGN KEY (guest_id)
                REFERENCES guests(guest_id)
        );
    """)

    # ---------------------------------------------------------
    # INCIDENTS
    # Operational problems affecting a property / reservation.
    # ---------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incidents (
            incident_id TEXT PRIMARY KEY,

            property_id VARCHAR(64) NOT NULL,
            booking_id VARCHAR(64),

            category VARCHAR(100) NOT NULL,
            description TEXT NOT NULL,

            severity VARCHAR(50) NOT NULL DEFAULT 'medium',
            status VARCHAR(50) NOT NULL DEFAULT 'open',

            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            resolved_at DATETIME,

            FOREIGN KEY (property_id)
                REFERENCES properties(property_id),

            FOREIGN KEY (booking_id)
                REFERENCES bookings(booking_id)
        );
    """)

    # ---------------------------------------------------------
    # ESCALATIONS
    # Human hand-offs created when the agent should not or
    # cannot continue autonomously.
    # ---------------------------------------------------------
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS escalations (
        escalation_id TEXT PRIMARY KEY,

        booking_id VARCHAR(64),
        property_id VARCHAR(64) NOT NULL,
        incident_id TEXT,

        category VARCHAR(100) NOT NULL DEFAULT 'other',
        reason TEXT NOT NULL,

        priority VARCHAR(50) NOT NULL DEFAULT 'medium',
        status VARCHAR(50) NOT NULL DEFAULT 'open',

        assigned_to VARCHAR(64),

        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        resolved_at DATETIME,

        FOREIGN KEY (booking_id)
            REFERENCES bookings(booking_id),

        FOREIGN KEY (property_id)
            REFERENCES properties(property_id),

        FOREIGN KEY (incident_id)
            REFERENCES incidents(incident_id),

        FOREIGN KEY (assigned_to)
            REFERENCES teams(team_id)
    );
""")
    connection.commit()


def create_indexes(connection: sqlite3.Connection):
    cursor = connection.cursor()

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_access_property
        ON access_systems(property_id);
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_booking
        ON messages(booking_id);
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_guest
        ON messages(guest_id);
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_incidents_property
        ON incidents(property_id);
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_incidents_booking
        ON incidents(booking_id);
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_escalations_status
        ON escalations(status);
    """)

    connection.commit()


def seed_access_systems(connection: sqlite3.Connection):
    """
    Create one fake access system for every property already
    present in the Hugging Face dataset.
    """

    cursor = connection.cursor()

    cursor.execute("""
        SELECT property_id
        FROM properties
        ORDER BY property_id;
    """)

    properties = cursor.fetchall()

    access_types = [
        ("smart_lock", "DemoLock", "lockbox", 1),
        ("smart_lock", "KeyCloud", "physical_key", 1),
        ("keypad", "EntryPad", "lockbox", 0),
    ]

    for index, (property_id,) in enumerate(properties):
        access_type, provider, backup_method, can_reset = (
            access_types[index % len(access_types)]
        )

        access_id = f"access_{property_id}"
        lock_id = f"lock_{property_id}"

        cursor.execute("""
            INSERT OR IGNORE INTO access_systems (
                access_id,
                property_id,
                access_type,
                provider,
                lock_id,
                backup_method,
                agent_can_reset,
                guest_verification_required,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            access_id,
            property_id,
            access_type,
            provider,
            lock_id,
            backup_method,
            can_reset,
            1,
            "online",
        ))

    connection.commit()


def seed_demo_scenario(connection: sqlite3.Connection):
    """
    Add a small demo conversation + incident using a real booking
    from the imported dataset.

    This gives us something useful when we build the first agent.
    """

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            booking_id,
            guest_id,
            property_id
        FROM bookings
        WHERE book_status = 'confirmed'
        LIMIT 1;
    """)

    booking = cursor.fetchone()

    if booking is None:
        print("No confirmed booking found. Skipping demo scenario.")
        return

    booking_id, guest_id, property_id = booking

    # Initial guest message
    cursor.execute("""
        INSERT OR IGNORE INTO messages (
            message_id,
            booking_id,
            guest_id,
            sender_type,
            message_text,
            channel
        )
        VALUES (?, ?, ?, ?, ?, ?);
    """, (
        "msg_demo_001",
        booking_id,
        guest_id,
        "guest",
        "Hi, I'm outside the apartment and the door code isn't working.",
        "chat",
    ))

    # Existing operational incident
    cursor.execute("""
        INSERT OR IGNORE INTO incidents (
            incident_id,
            property_id,
            booking_id,
            category,
            description,
            severity,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """, (
        "inc_demo_001",
        property_id,
        booking_id,
        "access",
        "Guest reported that the property access code is not working.",
        "high",
        "open",
    ))

    connection.commit()


def print_summary(connection: sqlite3.Connection):
    cursor = connection.cursor()

    tables = [
        "access_systems",
        "messages",
        "incidents",
        "escalations",
    ]

    print("\nStayOps tables")
    print("=" * 40)

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]

        print(f"{table:<20} {count} rows")


def main():
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}\n"
            "Run create_db.py first."
        )

    connection = sqlite3.connect(DB_PATH)

    # SQLite does not enforce foreign keys by default.
    connection.execute("PRAGMA foreign_keys = ON;")

    try:
        create_tables(connection)
        create_indexes(connection)

        seed_access_systems(connection)
        seed_demo_scenario(connection)

        print_summary(connection)

        print("\nStayOps tables added successfully.")

    finally:
        connection.close()


if __name__ == "__main__":
    main()




"""
                    STAYOPS DATABASE

Guests ──────┐
             ▼
         Bookings ──────────────┐
             │                  │
             ▼                  ▼
         Properties ─────► Access Systems
             │
             ├──────────► Incidents
             │
             └──────────► Tasks

Guests / Bookings
       │
       ▼
    Messages

Incidents / Bookings / Properties
       │
       ▼
   Escalations

Teams ◄──── assigned human operator


"""