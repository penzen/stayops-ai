from services.messages import send_message, get_booking_messages
from services.incidents import create_incident
from services.tasks import create_task, get_open_tasks
from services.escalations import create_escalation


BOOKING_ID = "book_0014"
GUEST_ID = "gst_2631"
PROPERTY_ID = "prop_15"


print("\n1. SENDING MESSAGE")
print("=" * 60)

message = send_message(
    booking_id=BOOKING_ID,
    guest_id=GUEST_ID,
    sender_type="agent",
    message_text=(
        "Hi Liliane, I'm checking the access issue now. "
        "Please stay near the property while I investigate."
    ),
)

print(message)


print("\n2. CREATING INCIDENT")
print("=" * 60)

incident = create_incident(
    property_id=PROPERTY_ID,
    booking_id=BOOKING_ID,
    category="access",
    description="Guest unable to enter property using smart lock.",
    severity="high",
)

print(incident)


print("\n3. CREATING OPERATIONAL TASK")
print("=" * 60)

task = create_task(
    property_id=PROPERTY_ID,
    booking_id=BOOKING_ID,
    category="maintenance",
    title="Investigate smart lock access failure",
)

print(task)


print("\n4. CREATING HUMAN ESCALATION")
print("=" * 60)

escalation = create_escalation(
    booking_id=BOOKING_ID,
    property_id=PROPERTY_ID,
    incident_id=incident["incident_id"],
    reason=(
        "Guest cannot access property. "
        "Automated recovery has not resolved the issue."
    ),
    priority="high",
)

print(escalation)


print("\n5. CONVERSATION HISTORY")
print("=" * 60)

messages = get_booking_messages(BOOKING_ID)

for message in messages:
    print(message)


print("\n6. OPEN TASKS")
print("=" * 60)

tasks = get_open_tasks(PROPERTY_ID)

for task in tasks:
    print(task)