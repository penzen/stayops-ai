from backend.services.tasks import create_task_if_missing


PROPERTY_ID = "prop_15"
BOOKING_ID = "book_demo_current_001"


def test_create_task_if_missing_reuses_existing_task(test_db):
    first_result = create_task_if_missing(
        property_id=PROPERTY_ID,
        booking_id=BOOKING_ID,
        category="heating",
        title="Investigate heating failure",
    )

    second_result = create_task_if_missing(
        property_id=PROPERTY_ID,
        booking_id=BOOKING_ID,
        category="heating",
        title="Investigate heating failure again",
    )

    assert first_result["created"] is True
    assert first_result["reason"] == "task_created"

    assert second_result["created"] is False
    assert second_result["reason"] == "existing_open_task"

    assert (
        first_result["task"]["task_id"]
        == second_result["task"]["task_id"]
    )

"""
First request
    ↓
No matching open heating task
    ↓
CREATE TASK
    ↓
created = True

Second request
    ↓
Matching open heating task exists
    ↓
REUSE TASK
    ↓
created = False
    ↓
same task_id ✓
    
    
"""