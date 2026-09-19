import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

from agents import Agent, Runner, trace
from agents.mcp import MCPServerStdio

from backend.agent.instructions import GUEST_AGENT_INSTRUCTIONS


load_dotenv(override=True)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


async def main():
    # Start our own StayOps MCP server as a subprocess.
    async with MCPServerStdio(
        name="StayOps Operations",
        params={
            "command": sys.executable,
            "args": [
                "-m",
                "backend.mcp.server",
            ],
            "cwd": str(PROJECT_ROOT),
        },
        cache_tools_list=True,
        client_session_timeout_seconds=30,
    ) as server:

        # -----------------------------------------------------
        # MCP TOOL DISCOVERY
        # -----------------------------------------------------

        tools = await server.list_tools()

        print("\nMCP TOOLS DISCOVERED")
        print("=" * 60)

        for tool in tools:
            print(f"- {tool.name}")

        # -----------------------------------------------------
        # AGENT
        # -----------------------------------------------------

        guest_operations_agent = Agent(
            name="StayOps Guest Operations Agent",
            instructions=GUEST_AGENT_INSTRUCTIONS,

            # Notice:
            # NO local tools=[...] here.
            #
            # The agent gets capabilities from the MCP server.
            mcp_servers=[server],
        )

        request = """
        Guest ID: gst_2631
        Booking ID: book_demo_current_001

        Guest message:
        I'm outside the apartment and the door code isn't working.
        """

        with trace(
            "StayOps Guest Operations - MCP",
            group_id="book_demo_current_001",
            metadata={
                "guest_id": "gst_2631",
                "booking_id": "book_demo_current_001",
                "scenario": "guest_locked_out",
                "tool_transport": "mcp_stdio",
            },
        ):
            result = await Runner.run(
                guest_operations_agent,
                request,
            )

        print("\nFINAL OUTPUT")
        print("=" * 60)
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())