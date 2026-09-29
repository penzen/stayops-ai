from backend.agent.guest_agent import build_agent_request


def test_agent_request_includes_resolved_case_history():
    request = build_agent_request(
        guest_id="gst_2631",
        booking_id="book_demo_current_001",
        message="What is happening with my heating problem?",
        open_cases_text="None",
        recent_cases_text=(
            "- Case ID: case_heating_001\n"
            "  Category: heating\n"
            "  Status: resolved\n"
            "  Summary: Heating stopped working."
        ),
        recent_messages_text=(
            "AGENT: The heating case is still waiting "
            "for confirmation."
        ),
    )

    assert "RECENT CASE HISTORY" in request
    assert "Status: resolved" in request
    assert "Category: heating" in request