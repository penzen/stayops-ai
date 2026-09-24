from backend.services.messages import (
    get_booking_messages,
    send_message,
)


BOOKING_ID = "book_demo_current_001"
GUEST_ID = "gst_2631"


def test_send_message_persists_message(test_db):
    messages_before = get_booking_messages(BOOKING_ID)

    message = send_message(
        booking_id=BOOKING_ID,
        guest_id=GUEST_ID,
        sender_type="guest",
        message_text="The heating is broken.",
    )

    messages_after = get_booking_messages(BOOKING_ID)

    assert message["booking_id"] == BOOKING_ID
    assert message["guest_id"] == GUEST_ID
    assert message["sender_type"] == "guest"
    assert message["message_text"] == "The heating is broken."

    assert len(messages_after) == len(messages_before) + 1

    saved_message = messages_after[-1]

    assert saved_message["message_id"] == message["message_id"]
    assert saved_message["message_text"] == "The heating is broken."


"""
send_message()
      ↓
returns message
      ↓
query SQLite again
      ↓
was it actually persisted?
      ↓
assert ✓
"""