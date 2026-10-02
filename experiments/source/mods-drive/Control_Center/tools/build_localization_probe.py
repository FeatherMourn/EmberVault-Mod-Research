"""Build a deterministic, research-only localization probe."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.research_lab import ResearchProbeService


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entries", type=Path, help="JSON object keyed by localization key and locale")
    parser.add_argument("output", type=Path)
    parser.add_argument("--build", default="unknown")
    parser.add_argument("--collection-probe", action="store_true", help="explicitly enable collection mutation research")
    args = parser.parse_args()
    payload = json.loads(args.entries.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise SystemExit("entries must be a JSON object")
    result = ResearchProbeService.generate_localization(
        args.output, payload, args.build, collection_probe=args.collection_probe
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
