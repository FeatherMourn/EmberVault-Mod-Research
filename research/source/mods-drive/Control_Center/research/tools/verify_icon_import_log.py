"""Verify the evidence chain for a runtime-imported custom UI icon."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


REQUIRED = {
    "IMPORTED_ICON": re.compile(r"ok=true\|result=([0-9a-f-]{36})"),
    "REGISTERED": re.compile(r"itemId=(\d+)\|recipeId=(\d+)"),
    "UI_LINKS": re.compile(r"UI_LINKS\|([1-9]\d*)\|matching_sets=([1-9]\d*)"),
}


def verify(path: Path, prefix: str) -> dict[str, object]:
    found: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            record = json.loads(raw)
        except json.JSONDecodeError:
            continue
        message = str(record.get("fields", {}).get("message", ""))
        if not message.startswith(prefix):
            continue
        for key, pattern in REQUIRED.items():
            match = pattern.search(message)
            if match:
                found[key] = match.group(0)
    missing = sorted(set(REQUIRED) - set(found))
    return {"valid": not missing, "prefix": prefix, "evidence": found, "missing": missing}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=Path)
    parser.add_argument("--prefix", default="[CC-COMBINED-LOCALIZED-BED] ")
    args = parser.parse_args()
    result = verify(args.log, args.prefix)
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

