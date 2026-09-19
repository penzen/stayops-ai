import asyncio
import json
from pathlib import Path

from agents.mcp import MCPServerStdio


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_PATH = (
    PROJECT_ROOT
    / "knowledge"
    / "str_ops"
    / "data"
    / "str-ops-corpus.jsonl"
)

QDRANT_PATH = PROJECT_ROOT / "memory" / "qdrant"


def chunk_text(
    text: str,
    chunk_size: int = 1800,
    overlap: int = 250,
) -> list[str]:
    """
    Split long documents into overlapping chunks before storing them.

    Qdrant handles embeddings and vector search,
    but we still decide how large each stored text chunk should be.
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
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found:\n{DATA_PATH}"
        )

    QDRANT_PATH.mkdir(parents=True, exist_ok=True)

    qdrant_params = {
        "command": "uvx",
        "args": ["mcp-server-qdrant"],
        "env": {
            "QDRANT_LOCAL_PATH": str(QDRANT_PATH),
            "COLLECTION_NAME": "stayops_knowledge",
            "EMBEDDING_MODEL": (
                "sentence-transformers/all-MiniLM-L6-v2"
            ),
            "TOOL_STORE_DESCRIPTION": (
                "Store trusted short-term-rental operational "
                "knowledge for later retrieval."
            ),
            "TOOL_FIND_DESCRIPTION": (
                "Search trusted short-term-rental operational "
                "knowledge for maintenance, inspections, cleaning, "
                "safety, procedures, and operational guidance."
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

        documents = []

        with DATA_PATH.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                if line:
                    documents.append(json.loads(line))

        print(f"\nLoaded {len(documents)} documents.")

        stored_chunks = 0

        for document in documents:
            text = document.get("text", "")
            chunks = chunk_text(text)

            for chunk_index, chunk in enumerate(chunks):
                metadata = {
                    "source_type": "str_ops",
                    "document_id": document.get("id"),
                    "title": document.get("title"),
                    "url": document.get("url"),
                    "source": document.get("source"),
                    "chunk_index": chunk_index,
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
                        f"Failed on document "
                        f"{document.get('id')} "
                        f"chunk {chunk_index}"
                    )
                    print(result)
                    return

                stored_chunks += 1

                if stored_chunks % 25 == 0:
                    print(
                        f"Stored {stored_chunks} chunks..."
                    )

        print("\nINGESTION COMPLETE")
        print("=" * 60)
        print(f"Documents: {len(documents)}")
        print(f"Chunks stored: {stored_chunks}")


if __name__ == "__main__":
    asyncio.run(main())





"""
STR-Ops JSONL
      ↓
read each document
      ↓
split document into chunks
      ↓
qdrant-store
      ↓
local embedding model
      ↓
vector stored in Qdrant



"""