import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_QDRANT_PATH = PROJECT_ROOT / "memory" / "qdrant"
SOPS_PATH = PROJECT_ROOT / "knowledge" / "stayops_sops"


def get_qdrant_path() -> Path:
    custom_path = os.getenv("STAYOPS_QDRANT_PATH")

    if custom_path:
        return Path(custom_path).resolve()

    return DEFAULT_QDRANT_PATH


def run_module(module: str, *args: str, env: dict[str, str]) -> None:
    subprocess.run(
        [sys.executable, "-m", module, *args],
        cwd=PROJECT_ROOT,
        env=env,
        check=True,
    )


def bootstrap_qdrant(qdrant_path: Path, force: bool = False) -> None:
    qdrant_path = qdrant_path.resolve()

    if qdrant_path.exists():
        if not force:
            raise FileExistsError(
                f"Qdrant directory already exists: {qdrant_path}\n"
                "Use --force if you want to rebuild it."
            )

        shutil.rmtree(qdrant_path)

    qdrant_path.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["STAYOPS_QDRANT_PATH"] = str(qdrant_path)

    print(f"\nBuilding Qdrant knowledge store: {qdrant_path}")

    print("\nIngesting STR-Ops corpus...")
    run_module(
        "backend.rag.ingest_str_ops",
        env=env,
    )

    sop_files = sorted(SOPS_PATH.glob("*.md"))

    if not sop_files:
        raise FileNotFoundError(f"No StayOps SOP files found in {SOPS_PATH}")

    for sop_file in sop_files:
        print(f"\nIngesting StayOps SOP: {sop_file.name}")
        run_module(
            "backend.rag.ingest_stayops_sops",
            sop_file.name,
            env=env,
        )

    print("\n" + "=" * 60)
    print("QDRANT BOOTSTRAP COMPLETE")
    print("=" * 60)
    print(f"Qdrant path: {qdrant_path}")
    print(f"StayOps SOPs ingested: {len(sop_files)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the StayOps Qdrant knowledge store from source files."
    )
    parser.add_argument(
        "--qdrant-path",
        type=Path,
        default=get_qdrant_path(),
        help="Directory where the Qdrant store will be created.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete and rebuild the Qdrant store if it already exists.",
    )

    args = parser.parse_args()

    bootstrap_qdrant(
        qdrant_path=args.qdrant_path,
        force=args.force,
    )


if __name__ == "__main__":
    main()