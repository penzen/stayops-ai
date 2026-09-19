from dotenv import load_dotenv

from agents import Agent, Runner, trace

from backend.agent.instructions import GUEST_AGENT_INSTRUCTIONS
from backend.agent.tools import (
    lookup_guest,
    lookup_reservation,
    lookup_property,
    lookup_access_system,
    lookup_open_incidents,
    check_guest_access_permission,
    message_guest,
    create_operations_task,
    escalate_to_human,
)


load_dotenv(override=True)


guest_operations_agent = Agent(
    name="StayOps Guest Operations Agent",
    instructions=GUEST_AGENT_INSTRUCTIONS,
    tools=[
        lookup_guest,
        lookup_reservation,
        lookup_property,
        lookup_access_system,
        lookup_open_incidents,
        check_guest_access_permission,
        message_guest,
        create_operations_task,
        escalate_to_human,
    ],
)


def main():
    request = """
    Guest ID: gst_2631
    Booking ID: book_demo_current_001

    Guest message:
    I'm outside the apartment and the door code isn't working.
    """

    with trace(
        "StayOps Guest Operations",
        group_id="book_demo_current_001",
        metadata={
            "guest_id": "gst_2631",
            "booking_id": "book_demo_current_001",
            "scenario": "guest_locked_out",
        },
    ):
        result = Runner.run_sync(
            guest_operations_agent,
            request,
        )

    print("\nFINAL OUTPUT")
    print("=" * 60)
    print(result.final_output)


if __name__ == "__main__":
    main()