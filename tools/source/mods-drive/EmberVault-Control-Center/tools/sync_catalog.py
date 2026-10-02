"""Export a validated EmberVault catalog into a repository-ready directory."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.application import EmbervaultRuntime


def main() -> int:
    parser = argparse.ArgumentParser(description="Write a validated EmberVault catalog snapshot")
    parser.add_argument("destination", type=Path, help="Repository folder that will receive embervault-catalog.json")
    # The repository root contains the reviewed adapter and seeded knowledge
    # assets. Using it by default makes the documented handoff complete; a
    # separate data root remains available for isolated/test exports.
    parser.add_argument("--data-root", type=Path, default=ROOT)
    args = parser.parse_args()
    runtime = EmbervaultRuntime.create(args.data_root)
    destination = runtime.catalog.sync_to_directory(args.destination)
    print(f"Catalog written: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
