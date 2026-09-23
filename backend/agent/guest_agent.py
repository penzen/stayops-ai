import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio

from backend.agent.instructions import GUEST_AGENT_INSTRUCTIONS


load_dotenv(override=True)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

QDRANT_PATH = PROJECT_ROOT / "memory" / "qdrant"


async def run_guest_agent(
    guest_id: str,
    booking_id: str,
    message: str,
    scenario_name: str = "guest_operations",
    show_tools: bool = False,
    db_path: str | Path | None = None,
):
    """
    Run the StayOps Guest Operations Agent for one guest message.

    This function is reusable by:
    - manual demos
    - evaluation scenarios
    - future API endpoints

    db_path:
        Optional database override.

        If supplied, the operational MCP server will use that
        database through STAYOPS_DB_PATH.

        If omitted, StayOps uses the normal stayops.db database.
    """

    # ---------------------------------------------------------
    # STAYOPS OPERATIONAL MCP SERVER
    # ---------------------------------------------------------

    operations_env = os.environ.copy()

    if db_path is not None:
        operations_env["STAYOPS_DB_PATH"] = str(
            Path(db_path).resolve()
        )

    operations_params = {
        "command": sys.executable,
        "args": [
            "-m",
            "backend.mcp.server",
        ],
        "cwd": str(PROJECT_ROOT),
        "env": operations_env,
    }

    # ---------------------------------------------------------
    # QDRANT KNOWLEDGE MCP SERVER
    # ---------------------------------------------------------

    knowledge_params = {
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
    }

    async with MCPServerStdio(
        name="StayOps Operations",
        params=operations_params,
        cache_tools_list=True,
        client_session_timeout_seconds=60,
    ) as operations_server:

        async with MCPServerStdio(
            name="StayOps Knowledge",
            params=knowledge_params,
            cache_tools_list=True,
            client_session_timeout_seconds=120,
        ) as knowledge_server:

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

            request = f"""
Guest ID: {guest_id}
Booking ID: {booking_id}

Guest message:
{message}
"""

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