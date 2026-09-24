from backend.services.cases import (
    ensure_case,
    get_case_context,
)
from backend.services.tasks import create_task_if_missing
from backend.services.escalations import create_escalation_if_missing
from backend.services.messages import send_message


PROPERTY_ID = "prop_15"
BOOKING_ID = "book_demo_current_001"
GUEST_ID = "gst_2631"


def test_get_case_context_returns_operational_state(test_db):
    case_result = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Guest reported that heating is not working.",
    )

    case_id = case_result["case"]["case_id"]

    task_result = create_task_if_missing(
        property_id=PROPERTY_ID,
        booking_id=BOOKING_ID,
        category="heating",
        title="Investigate heating failure",
        case_id=case_id,
    )

    escalation_result = create_escalation_if_missing(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        reason="Heating failure requires operational attention.",
        priority="high",
        case_id=case_id,
    )

    send_message(
        booking_id=BOOKING_ID,
        guest_id=GUEST_ID,
        sender_type="guest",
        message_text="The heating is still broken.",
    )

    send_message(
        booking_id=BOOKING_ID,
        guest_id=GUEST_ID,
        sender_type="agent",
        message_text="We are following up on the heating issue.",
    )

    context = get_case_context(case_id)

    assert context is not None

    assert context["case"]["case_id"] == case_id
    assert context["case"]["category"] == "heating"

    assert len(context["tasks"]) == 1
    assert (
        context["tasks"][0]["task_id"]
        == task_result["task"]["task_id"]
    )

    assert len(context["escalations"]) == 1
    assert (
        context["escalations"][0]["escalation_id"]
        == escalation_result["escalation"]["escalation_id"]
    )

    message_texts = [
        message["message_text"]
        for message in context["recent_messages"]
    ]

    assert "The heating is still broken." in message_texts

    assert (
        "We are following up on the heating issue."
        in message_texts
    )

def test_get_case_context_keeps_case_work_separate(test_db):
    heating_case = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="heating",
        summary="Heating is broken.",
    )

    refund_case = ensure_case(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="refund",
        summary="Guest requested a refund.",
    )

    heating_case_id = heating_case["case"]["case_id"]
    refund_case_id = refund_case["case"]["case_id"]

    heating_task = create_task_if_missing(
        property_id=PROPERTY_ID,
        booking_id=BOOKING_ID,
        category="heating",
        title="Investigate heating failure",
        case_id=heating_case_id,
    )

    refund_escalation = create_escalation_if_missing(
        booking_id=BOOKING_ID,
        property_id=PROPERTY_ID,
        category="refund",
        reason="Refund requires human review.",
        priority="high",
        case_id=refund_case_id,
    )

    heating_context = get_case_context(heating_case_id)
    refund_context = get_case_context(refund_case_id)
    assert heating_context is not None
    assert refund_context is not None

    assert len(heating_context["tasks"]) == 1
    assert (
        heating_context["tasks"][0]["task_id"]
        == heating_task["task"]["task_id"]
    )

    assert heating_context["escalations"] == []

    assert refund_context["tasks"] == []

    assert len(refund_context["escalations"]) == 1
    assert (
        refund_context["escalations"][0]["escalation_id"]
        == refund_escalation["escalation"]["escalation_id"]
    )