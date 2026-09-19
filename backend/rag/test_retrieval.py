import asyncio
import argparse
from pathlib import Path

from agents.mcp import MCPServerStdio


PROJECT_ROOT = Path(__file__).resolve().parents[2]
QDRANT_PATH = PROJECT_ROOT / "memory" / "qdrant"


async def main():
    qdrant_params = {
        "command": "uvx",
        "args": ["mcp-server-qdrant"],
        "env": {
            "QDRANT_LOCAL_PATH": str(QDRANT_PATH),
            "COLLECTION_NAME": "stayops_knowledge",
            "QDRANT_READ_ONLY": "true",
        },
    }

    async with MCPServerStdio(
        name="StayOps Knowledge",
        params=qdrant_params,
        client_session_timeout_seconds=120,
    ) as server:

        tools = await server.list_tools()

        print("\nTOOLS DISCOVERED")
        print("=" * 60)

        for tool in tools:
            print(f"- {tool.name}")

        result = await server.call_tool(
            "qdrant-find",
            {
                "query": (
                    "Guest says the heating has been broken all evening "
                    "and wants a full refund. What should StayOps do?"
                )
            },
        )

        print("\nSEARCH RESULT")
        print("=" * 60)

        for item in result:
            print(item)


if __name__ == "__main__":
    asyncio.run(main())