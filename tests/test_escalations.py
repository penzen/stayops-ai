from backend.services.escalations import create_escalation_if_missing


PROPERTY_ID = "prop_15"
BOOKING_ID = "book_demo_current_001"


def test_create_escalation_if_missing_reuses_existing_escalation(test_db):
    first_result = create_escalation_if_missing(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        reason="Heating failure requires human assistance.",
        priority="high",
    )

    second_result = create_escalation_if_missing(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        reason="Second attempt to escalate the same heating issue.",
        priority="high",
    )

    assert first_result["created"] is True
    assert first_result["reason"] == "escalation_created"

    assert second_result["created"] is False
    assert second_result["reason"] == "existing_open_escalation"

    assert (
        first_result["escalation"]["escalation_id"]
        == second_result["escalation"]["escalation_id"]
    )


"""
Agent asks for escalation
        ↓
No matching open escalation
        ↓
CREATE
        ↓
Agent asks again
        ↓
Matching escalation already exists
        ↓
REUSE
        ↓
No duplicate human handoff ✓

"""