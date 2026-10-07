from backend.agent.guest_agent import build_agent_request


def test_agent_request_includes_preloaded_operational_context():
    request = build_agent_request(
        guest_id="gst_2631",
        booking_id="book_demo_current_001",
        message="The heating is broken.",
        open_cases_text="None",
        recent_cases_text="None",
        recent_messages_text="None",
        guest_text='{"guest_id": "gst_2631", "name": "Liliane"}',
        reservation_text=(
            '{"booking_id": "book_demo_current_001", '
            '"property_id": "prop_001"}'
        ),
        property_text=(
            '{"property_id": "prop_001", '
            '"city": "Berlin"}'
        ),
    )

    assert "PRELOADED OPERATIONAL CONTEXT" in request
    assert '"guest_id": "gst_2631"' in request
    assert '"booking_id": "book_demo_current_001"' in request
    assert '"property_id": "prop_001"' in request
    assert "OPEN OPERATIONAL CASES" in request
