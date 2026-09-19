import asyncio
from pathlib import Path
import argparse

from agents.mcp import MCPServerStdio


PROJECT_ROOT = Path(__file__).resolve().parents[2]

SOPS_PATH = (
    PROJECT_ROOT
    / "knowledge"
    / "stayops_sops"
)

QDRANT_PATH = (
    PROJECT_ROOT
    / "memory"
    / "qdrant"
)


def chunk_text(
    text: str,
    chunk_size: int = 1400,
    overlap: int = 200,
) -> list[str]:
    """
    Split StayOps SOPs into smaller overlapping chunks.
    """

    text = text.strip()

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - overlap

    return chunks


async def main():
    if not SOPS_PATH.exists():
        raise FileNotFoundError(
            f"SOP directory not found:\n{SOPS_PATH}"
        )

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "filename",
        help="Name of the StayOps SOP markdown file to ingest.",
    )

    args = parser.parse_args()

    sop_file = SOPS_PATH / args.filename

    if not sop_file.exists():
        raise FileNotFoundError(
            f"SOP file not found:\n{sop_file}"
        )

    sop_files = [sop_file]

    qdrant_params = {
        "command": "uvx",
        "args": [
            "mcp-server-qdrant",
        ],
        "env": {
            "QDRANT_LOCAL_PATH": str(QDRANT_PATH),
            "COLLECTION_NAME": "stayops_knowledge",
            "EMBEDDING_MODEL": (
                "sentence-transformers/all-MiniLM-L6-v2"
            ),
        },
    }

    async with MCPServerStdio(
        name="StayOps Knowledge Store",
        params=qdrant_params,
        client_session_timeout_seconds=120,
    ) as server:

        tools = await server.list_tools()

        print("\nQDRANT TOOLS")
        print("=" * 60)

        for tool in tools:
            print(f"- {tool.name}")

        stored_chunks = 0

        for sop_file in sop_files:
            text = sop_file.read_text(
                encoding="utf-8"
            )

            chunks = chunk_text(text)

            print(
                f"\nProcessing {sop_file.name}: "
                f"{len(chunks)} chunks"
            )

            for chunk_index, chunk in enumerate(chunks):

                metadata = {
                    "source_type": "stayops_sop",
                    "document_id": sop_file.stem,
                    "title": sop_file.stem.replace(
                        "_",
                        " ",
                    ).title(),
                    "filename": sop_file.name,
                    "chunk_index": chunk_index,
                    "authority": "internal_approved",
                }

                result = await server.call_tool(
                    "qdrant-store",
                    {
                        "information": chunk,
                        "metadata": metadata,
                    },
                )

                if result.is_error:
                    print(
                        f"Failed to store "
                        f"{sop_file.name} "
                        f"chunk {chunk_index}"
                    )
                    print(result)
                    return

                stored_chunks += 1

        print("\nSOP INGESTION COMPLETE")
        print("=" * 60)
        print(f"SOP files: {len(sop_files)}")
        print(f"Chunks stored: {stored_chunks}")


if __name__ == "__main__":
    asyncio.run(main())