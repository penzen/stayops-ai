# StayOps Services Layer

## Overview

The `services` folder contains the **deterministic business logic used to interact with the StayOps operational database**.

Its purpose is to create a clean boundary between:

* the database
* FastAPI
* AI agents
* MCP tools
* evaluation code
* other application components

Instead of allowing every component to write SQL queries directly, the application interacts with the database through small Python service functions.

The basic architecture is:

```text
               StayOps Application

                     User
                      │
                      ▼
                 AI Agent
                      │
                      ▼
                Tools / MCP
                      │
                      ▼
              ┌──────────────┐
              │   SERVICES   │
              └──────┬───────┘
                     │
                     ▼
              SQLite / Postgres
```

The service layer therefore acts as the interface between the application and the operational database.

---

# Why We Added a Service Layer

Without a service layer, different parts of the application could start writing SQL directly.

For example:

```text
Agent ─────────────► SQL
FastAPI ───────────► SQL
MCP Server ────────► SQL
Evaluation code ───► SQL
```

This creates several problems.

SQL logic becomes duplicated.

Database implementation details leak into the AI system.

Changing the database becomes difficult.

Testing becomes harder.

Permissions and business rules become harder to enforce consistently.

Instead, StayOps uses:

```text
Agent ─────────────┐
FastAPI ───────────┤
MCP Server ────────┼──► Services ───► Database
Evaluations ───────┤
Frontend Backend ──┘
```

Every component uses the same service functions.

For example:

```python
get_guest("gst_2631")
```

rather than:

```python
SELECT *
FROM guests
WHERE guest_id = 'gst_2631';
```

The caller does not need to know how the information is stored.

---

# Current Folder Structure

```text
backend/
│
├── database/
│   ├── create_db.py
│   ├── add_stayops_tables.py
│   └── stayops.db
│
├── services/
│   ├── __init__.py
│   ├── db.py
│   ├── guests.py
│   ├── reservations.py
│   ├── properties.py
│   └── incidents.py
│
└── test_services.py
```

Each service file represents a specific part of the StayOps domain.

---

# `db.py`

`db.py` is responsible for opening database connections.

```python
from pathlib import Path
import sqlite3


DB_PATH = Path("backend/database/stayops.db")


def get_connection():
    connection = sqlite3.connect(DB_PATH)

    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")

    return connection
```

Instead of every service repeatedly writing:

```python
sqlite3.connect(...)
```

they all use:

```python
get_connection()
```

This gives us one central place for database configuration.

---

## Why `row_factory` Is Used

Normally SQLite returns rows as tuples:

```python
(
    "book_0014",
    "gst_2631",
    "prop_15",
    ...
)
```

That is inconvenient because we would need to remember what every position means.

By setting:

```python
connection.row_factory = sqlite3.Row
```

we can convert the result into a dictionary:

```python
{
    "booking_id": "book_0014",
    "guest_id": "gst_2631",
    "property_id": "prop_15"
}
```

This is much easier for:

```text
Agents
MCP tools
FastAPI
JSON responses
Evaluations
Debugging
```

---

## Foreign Keys

We also enable:

```python
connection.execute("PRAGMA foreign_keys = ON;")
```

SQLite does not enforce foreign-key relationships automatically.

StayOps relies heavily on relationships such as:

```text
guest
  │
  ▼
booking
  │
  ▼
property
```

so enforcing foreign keys helps prevent invalid data from entering the system.

---

# `guests.py`

This service handles guest information.

Current function:

```python
get_guest(guest_id)
```

Example:

```python
guest = get_guest("gst_2631")
```

Result:

```python
{
    "guest_id": "gst_2631",
    "first_name": "Liliane",
    "last_name": "Bavaud",
    "email": "liliane419@gmail.example",
    "phone": "0790000054",
    "guest_lang": "fr",
    "locale": "fr_CH",
    "guest_geo": "European_FR"
}
```

This gives the rest of the StayOps system a clean way to retrieve guest information.

Later this service may also contain functions such as:

```python
get_guest_by_email()
get_guest_by_phone()
verify_guest_identity()
```

---

# `reservations.py`

This service handles booking and reservation information.

Current functions:

```python
get_reservation()
get_guest_reservations()
```

Example:

```python
booking = get_reservation("book_0014")
```

Result:

```python
{
    "booking_id": "book_0014",
    "guest_id": "gst_2631",
    "property_id": "prop_15",
    "check_in": "2026-01-03 15:00:00",
    "check_out": "2026-01-05 11:00:00",
    "nights": 2,
    "total_price": 1263.73,
    "book_status": "confirmed",
    "source": "Booking.com",
    "assigned_to": "GRO_254"
}
```

Reservation information is particularly important because many future agent actions should only happen after a reservation has been verified.

For example:

```text
Guest asks for access information
             │
             ▼
       Find reservation
             │
             ▼
       Is it confirmed?
             │
             ▼
    Is this their property?
             │
             ▼
    Is check-in permitted?
             │
             ▼
   Continue with access workflow
```

This is one of our first **safety boundaries**.

The AI should not simply trust someone claiming to be a guest.

---

# `properties.py`

This service currently handles two different but closely related things:

```python
get_property()
get_access_system()
```

## Property Lookup

Example:

```python
get_property("prop_15")
```

returns:

```python
{
    "property_id": "prop_15",
    "title": "Premium Business Flat near La Défense (Neuilly)",
    "city": "Paris",
    "max_guests": 2,
    "base_price": 489.0,
    ...
}
```

This represents the physical rental property.

---

## Access System Lookup

The same property can also have an associated access configuration.

Example:

```python
get_access_system("prop_15")
```

returns:

```python
{
    "access_id": "access_prop_15",
    "property_id": "prop_15",
    "access_type": "smart_lock",
    "provider": "KeyCloud",
    "lock_id": "lock_prop_15",
    "backup_method": "physical_key",
    "agent_can_reset": 1,
    "guest_verification_required": 1,
    "status": "online"
}
```

This is important because property information and access-system information are different concepts.

```text
Property
   │
   ├── address
   ├── capacity
   ├── price
   └── property type

Access system
   │
   ├── lock type
   ├── provider
   ├── lock ID
   ├── backup method
   ├── agent permissions
   └── verification requirements
```

Keeping them separate allows access systems to change without changing the property itself.

---

# `incidents.py`

This service handles operational problems.

Current function:

```python
get_open_incidents(property_id)
```

Example:

```python
get_open_incidents("prop_15")
```

currently returns:

```python
[
    {
        "incident_id": "inc_demo_001",
        "property_id": "prop_15",
        "booking_id": "book_0014",
        "category": "access",
        "description": "Guest reported that the property access code is not working.",
        "severity": "high",
        "status": "open",
        "resolved_at": None
    }
]
```

This allows the system to determine whether a problem has already been reported.

For example:

```text
Guest:
"My door code isn't working."

          │
          ▼

Check property incidents

          │
          ▼

Existing access incident found

          │
          ▼

Agent now has additional context
```

Without incident information, the agent might incorrectly assume that the guest is the only person experiencing the problem.

Eventually this service will also perform actions such as:

```python
create_incident()
update_incident()
resolve_incident()
```

---

# What `test_services.py` Did

`test_services.py` was a simple integration test.

It started with:

```python
booking = get_reservation("book_0014")
```

which returned:

```text
book_0014
│
├── guest_id = gst_2631
│
└── property_id = prop_15
```

Then we followed those relationships.

```text
                      book_0014
                          │
              ┌───────────┴───────────┐
              │                       │
              ▼                       ▼
          gst_2631                  prop_15
              │                       │
              ▼              ┌────────┼─────────┐
      Liliane Bavaud          │        │         │
                              ▼        ▼         ▼
                         Property    Access    Incidents
                           Info      System
```

The test confirmed that all of these services can successfully work together.

The actual output showed:

```text
Booking
   ↓
book_0014

Guest
   ↓
Liliane Bavaud

Property
   ↓
Premium Business Flat near La Défense

Access System
   ↓
KeyCloud smart lock

Incident
   ↓
Door access code not working
```

This is essentially the data context that our first AI agent will eventually need.

---

# Why This Matters for the Agent

Suppose Liliane sends:

```text
"I'm outside the apartment and my door code isn't working."
```

The LLM itself does not know:

```text
Who Liliane is
Which property she booked
Whether her booking is valid
Which lock the property uses
Whether the agent can reset it
Whether an incident already exists
```

Instead, the agent will use tools.

Eventually the flow will look approximately like this:

```text
Guest message
     │
     ▼
Guest Operations Agent
     │
     ▼
get_reservation()
     │
     ▼
Reservations Service
     │
     ▼
Database
```

Then:

```text
Agent
  │
  ├──► get_guest()
  │
  ├──► get_property()
  │
  ├──► get_access_system()
  │
  └──► get_open_incidents()
```

The resulting context might be:

```text
Guest:
Liliane Bavaud

Reservation:
Confirmed

Property:
prop_15

Access:
KeyCloud smart lock

Agent reset permitted:
Yes

Guest verification required:
Yes

Current incidents:
Known access problem
```

The agent can then make a **bounded decision based on real operational state**.

---

# Deterministic Code vs AI

One of the main architectural ideas in StayOps is that we should not ask the LLM to do things normal software can determine reliably.

For example:

```text
"Does booking book_0014 exist?"
```

should not be answered by an LLM.

The database can answer it exactly.

Similarly:

```text
"Is the booking confirmed?"
"Which property is associated with this guest?"
"Does the property have an open incident?"
"Is the agent permitted to reset this lock?"
```

are deterministic questions.

The LLM becomes useful for questions such as:

```text
What is the guest trying to accomplish?

Which available capability should be used?

Is clarification required?

Does this situation appear resolved?

Should the workflow continue or escalate?
```

This gives us the principle:

> **Use deterministic software for facts and rules. Use AI for ambiguity and contextual decisions.**

---

# Future Architecture

As the project grows, these services will become the foundation for several components.

```text
                        Guest
                          │
                          ▼
                       FastAPI
                          │
                          ▼
                Guest Operations Agent
                          │
                          ▼
                      AI Tools
                          │
                          ▼
                     MCP Server
                          │
                          ▼
                 ┌────────────────┐
                 │    SERVICES    │
                 └───────┬────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
      Guests        Reservations     Properties
                                         │
                         ┌───────────────┼─────────────┐
                         ▼               ▼             ▼
                       Access        Incidents       Tasks
                         │
                         ▼
                     Database
```

The agent should never need to know whether the database underneath is:

```text
SQLite
PostgreSQL
RDS
or something else
```

It simply calls the capabilities provided by the service layer.

---

# Moving From SQLite to AWS

During local development we currently use:

```text
Services
   │
   ▼
SQLite
```

Later, the AWS version may use something such as:

```text
Services
   │
   ▼
PostgreSQL / RDS
```

If we keep database access isolated inside the service layer, much of the application above it can remain unchanged.

For example:

```python
get_reservation("book_0014")
```

can remain the same regardless of whether the data ultimately comes from SQLite or PostgreSQL.

This is another reason we created the service layer instead of letting the agent query SQLite directly.

---

# Current Read Capabilities

At this stage StayOps can retrieve:

```text
Guest information
        │
        ▼
Reservation information
        │
        ▼
Property information
        │
        ▼
Access configuration
        │
        ▼
Existing operational incidents
```

These are currently **read operations**.

The system can inspect the operational world, but it cannot yet change it.

---

# Next Stage: Action Services

The next step is to add actions such as:

```python
send_message()

create_incident()

create_escalation()

create_task()
```

This changes our backend from:

```text
READ THE WORLD
```

to:

```text
READ THE WORLD
      +
CHANGE THE WORLD
```

That distinction matters because this is where an autonomous system becomes more than a chatbot.

Eventually:

```text
Guest problem
     │
     ▼
Understand
     │
     ▼
Retrieve state
     │
     ▼
Make decision
     │
     ▼
Take action
     │
     ▼
State changes
     │
     ▼
Verify outcome
```

And that is the foundation of the StayOps project.
