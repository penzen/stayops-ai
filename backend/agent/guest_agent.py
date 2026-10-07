import asyncio
import json
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

from agents import Agent, Runner, trace
from agents.mcp import MCPServer, MCPServerStdio

from backend.agent.instructions import GUEST_AGENT_INSTRUCTIONS


load_dotenv(override=True)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_QDRANT_PATH = PROJECT_ROOT / "memory" / "qdrant"


def get_qdrant_path() -> Path:
    custom_path = os.getenv("STAYOPS_QDRANT_PATH")

    if custom_path:
        return Path(custom_path).resolve()

    return DEFAULT_QDRANT_PATH


QDRANT_PATH = get_qdrant_path()


def create_operations_mcp_server(
    db_path: str | Path | None = None,
) -> MCPServerStdio:
    operations_env = os.environ.copy()

    if db_path is not None:
        operations_env["STAYOPS_DB_PATH"] = str(
            Path(db_path).resolve()
        )

    return MCPServerStdio(
        name="StayOps Operations",
        params={
            "command": sys.executable,
            "args": [
                "-m",
                "backend.mcp.server",
            ],
            "cwd": str(PROJECT_ROOT),
            "env": operations_env,
        },
        cache_tools_list=True,
        client_session_timeout_seconds=60,
    )


def create_knowledge_mcp_server() -> MCPServerStdio:
    return MCPServerStdio(
        name="StayOps Knowledge",
        params={
            "command": "uvx",
            "args": [
                "mcp-server-qdrant",
            ],
            "env": {
                "QDRANT_LOCAL_PATH": str(QDRANT_PATH),
                "COLLECTION_NAME": "stayops_knowledge",
                "QDRANT_READ_ONLY": "true",
                "EMBEDDING_MODEL": (
                    "sentence-transformers/all-MiniLM-L6-v2"
                ),
            },
        },
        cache_tools_list=True,
        client_session_timeout_seconds=120,
    )


@asynccontextmanager
async def _borrow_mcp_server(server: MCPServer):
    # Reuse an MCP server whose lifecycle is owned by the caller.
    yield server

def build_agent_request(
    guest_id: str,
    booking_id: str,
    message: str,
    open_cases_text: str,
    recent_cases_text: str,
    recent_messages_text: str,
    guest_text: str = "Not preloaded",
    reservation_text: str = "Not preloaded",
    property_text: str = "Not preloaded",
) -> str:
    return f"""
        Guest ID: {guest_id}
        Booking ID: {booking_id}

        PRELOADED OPERATIONAL CONTEXT

        GUEST
        {guest_text}

        RESERVATION
        {reservation_text}

        PROPERTY
        {property_text}

        OPEN OPERATIONAL CASES

        {open_cases_text}

        RECENT CASE HISTORY

        {recent_cases_text}

        RECENT BOOKING CONVERSATION

        {recent_messages_text}

        CURRENT GUEST MESSAGE

        {message}
        """


async def run_guest_agent(
    guest_id: str,
    booking_id: str,
    message: str,
    scenario_name: str = "guest_operations",
    show_tools: bool = False,
    db_path: str | Path | None = None,
    open_cases: list[dict] | None = None,
    recent_cases: list[dict] | None = None,
    recent_messages: list[dict] | None = None,
    mcp_servers: list[MCPServer] | None = None,
    guest: dict | None = None,
    reservation: dict | None = None,
    property_data: dict | None = None,
):
    """
    Run the StayOps Guest Operations Agent for one guest message.

    This function is reusable by:
    - manual demos
    - evaluation scenarios
    - API endpoints

    db_path:
        Optional database override.

        If supplied, the operational MCP server will use that
        database through STAYOPS_DB_PATH.

        If omitted, StayOps uses the normal stayops.db database.

    open_cases:
        Optional list of currently open operational Cases for
        the booking.

    recent_cases:
        Optional bounded Case history for the booking, including
        resolved Cases used for historical follow-up questions.

    recent_messages:
        Optional bounded booking conversation history supplied
        as routing/context information for the agent.
    """

    # ---------------------------------------------------------
    # MCP SERVER LIFECYCLE
    # ---------------------------------------------------------

    if mcp_servers is None:
        operations_context = create_operations_mcp_server(
            db_path
        )
        knowledge_context = create_knowledge_mcp_server()
    else:
        if len(mcp_servers) != 2:
            raise ValueError(
                "StayOps expects exactly two MCP servers: "
                "operations and knowledge."
            )

        operations_context = _borrow_mcp_server(
            mcp_servers[0]
        )
        knowledge_context = _borrow_mcp_server(
            mcp_servers[1]
        )

    async with operations_context as operations_server:

        async with knowledge_context as knowledge_server:

            # -------------------------------------------------
            # OPTIONAL TOOL DEBUGGING
            # -------------------------------------------------

            if show_tools:
                print("\nOPERATIONS TOOLS")
                print("=" * 60)

                operations_tools = (
                    await operations_server.list_tools()
                )

                for tool in operations_tools:
                    print(f"- {tool.name}")

                print("\nKNOWLEDGE TOOLS")
                print("=" * 60)

                knowledge_tools = (
                    await knowledge_server.list_tools()
                )

                for tool in knowledge_tools:
                    print(f"- {tool.name}")

            # -------------------------------------------------
            # AGENT
            # -------------------------------------------------

            agent = Agent(
                name="StayOps Guest Operations Agent",
                instructions=GUEST_AGENT_INSTRUCTIONS,
                mcp_servers=[
                    operations_server,
                    knowledge_server,
                ],
            )

            # -------------------------------------------------
            # PRELOADED DETERMINISTIC CONTEXT
            # -------------------------------------------------

            guest_text = (
                json.dumps(
                    guest,
                    ensure_ascii=False,
                    default=str,
                )
                if guest is not None
                else "Not preloaded"
            )

            reservation_text = (
                json.dumps(
                    reservation,
                    ensure_ascii=False,
                    default=str,
                )
                if reservation is not None
                else "Not preloaded"
            )

            property_text = (
                json.dumps(
                    property_data,
                    ensure_ascii=False,
                    default=str,
                )
                if property_data is not None
                else "Not preloaded"
            )

            # -------------------------------------------------
            # OPEN CASE CONTEXT
            # -------------------------------------------------

            case_context_lines = []

            for case in open_cases or []:
                case_context_lines.append(
                    (
                        f"- Case ID: {case['case_id']}\n"
                        f"  Category: {case['category']}\n"
                        f"  Status: {case['status']}\n"
                        f"  Summary: "
                        f"{case.get('summary') or 'No summary'}"
                    )
                )

            open_cases_text = (
                "\n".join(case_context_lines)
                if case_context_lines
                else "None"
            )
            # -------------------------------------------------
            # RECENT CASE HISTORY
            # -------------------------------------------------

            recent_case_lines = []

            for case in recent_cases or []:
                recent_case_lines.append(
                    (
                        f"- Case ID: {case['case_id']}\n"
                        f"  Category: {case['category']}\n"
                        f"  Status: {case['status']}\n"
                        f"  Summary: "
                        f"{case.get('summary') or 'No summary'}"
                    )
                )

            recent_cases_text = (
                "\n".join(recent_case_lines)
                if recent_case_lines
                else "None"
            )

            # -------------------------------------------------
            # RECENT CONVERSATION CONTEXT
            # -------------------------------------------------

            message_context_lines = []

            for previous_message in recent_messages or []:
                sender_type = previous_message.get(
                    "sender_type",
                    "unknown",
                )

                message_text = previous_message.get(
                    "message_text",
                    "",
                )

                message_context_lines.append(
                    (
                        f"{sender_type.upper()}: "
                        f"{message_text}"
                    )
                )

            recent_messages_text = (
                "\n".join(message_context_lines)
                if message_context_lines
                else "None"
            )

            # -------------------------------------------------
            # AGENT REQUEST
            # -------------------------------------------------

            request = build_agent_request(
                    guest_id=guest_id,
                    booking_id=booking_id,
                    message=message,
                    open_cases_text=open_cases_text,
                    recent_cases_text=recent_cases_text,
                    recent_messages_text=recent_messages_text,
                    guest_text=guest_text,
                    reservation_text=reservation_text,
                    property_text=property_text,
                )

            # -------------------------------------------------
            # TRACE
            # -------------------------------------------------

            with trace(
                f"StayOps - {scenario_name}",
                group_id=booking_id,
                metadata={
                    "guest_id": guest_id,
                    "booking_id": booking_id,
                    "scenario": scenario_name,
                    "operations": "stayops_mcp",
                    "knowledge": "qdrant_mcp",
                    "database": (
                        str(db_path)
                        if db_path is not None
                        else "default"
                    ),
                },
            ):
                result = await Runner.run(
                    agent,
                    request,
                    max_turns=15,
                )

            return result


async def main():
    """
    Manual demo.

    No db_path is supplied here, so this uses the normal
    backend/database/stayops.db database.
    """

    result = await run_guest_agent(
        guest_id="gst_2631",
        booking_id="book_demo_current_001",
        message=(
            "The heating has been broken all evening. "
            "I want a full refund."
        ),
        scenario_name="manual_refund_demo",
        show_tools=True,
    )

    print("\nFINAL OUTPUT")
    print("=" * 60)
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())



"""
Guest:
"Water is leaking under the sink."

        ↓

lookup reservation
        ↓
Operations MCP / SQLite

        ↓

identify property

        ↓

search operational knowledge
        ↓
Qdrant MCP
        ↓
relevant leak / maintenance guidance

        ↓

agent combines both

        ↓

create maintenance task
        ↓

possibly escalate depending on severity

        ↓

message guest


"""