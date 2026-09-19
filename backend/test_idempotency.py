from services.tasks import create_task_if_missing
from services.escalations import create_escalation_if_missing


PROPERTY_ID = "prop_15"
BOOKING_ID = "book_demo_current_001"
INCIDENT_ID = "inc_21465ed282e8"


print("\nTASK TEST")
print("=" * 60)

task_1 = create_task_if_missing(
    property_id=PROPERTY_ID,
    booking_id=BOOKING_ID,
    category="access",
    title="Guest locked out; smart-lock code not working",
)

print(task_1)


print("\nTASK TEST AGAIN")
print("=" * 60)

task_2 = create_task_if_missing(
    property_id=PROPERTY_ID,
    booking_id=BOOKING_ID,
    category="access",
    title="Another attempt to create the same access task",
)

print(task_2)


print("\nESCALATION TEST")
print("=" * 60)

escalation_1 = create_escalation_if_missing(
    booking_id=BOOKING_ID,
    property_id=PROPERTY_ID,
    incident_id=INCIDENT_ID,
    reason="Guest requires human assistance with property access.",
    priority="high",
)

print(escalation_1)


print("\nESCALATION TEST AGAIN")
print("=" * 60)

escalation_2 = create_escalation_if_missing(
    booking_id=BOOKING_ID,
    property_id=PROPERTY_ID,
    incident_id=INCIDENT_ID,
    reason="Trying to create another escalation for the same incident.",
    priority="high",
)

print(escalation_2)