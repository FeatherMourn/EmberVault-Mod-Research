"""Resolve GUID-like dependencies for an extracted visual candidate."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

GUID_RE = re.compile(r"(?i)([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})")


def collect_guids(value: Any, path: str = "") -> list[dict[str, str]]:
    found: list[dict[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            found.extend(collect_guids(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(collect_guids(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        for match in GUID_RE.finditer(value):
            found.append({"path": path, "guid": match.group(1).lower()})
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("archive_root", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.candidate.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    index: dict[str, list[str]] = {}
    for path in args.archive_root.rglob("*.json"):
        match = GUID_RE.match(path.stem)
        if match:
            index.setdefault(match.group(1).lower(), []).append(str(path))
    references = collect_guids(data)
    unique = {}
    for item in references:
        unique.setdefault(item["guid"], {"guid": item["guid"], "paths": []})["paths"].append(item["path"])
    dependencies = []
    for guid in sorted(unique):
        matches = index.get(guid, [])
        dependencies.append({
            "guid": guid,
            "reference_paths": sorted(set(unique[guid]["paths"])),
            "available": bool(matches),
            "matches": sorted(matches),
        })
    report = {
        "schema": "control_center.visual_candidate_dependency_report.v1",
        "candidate": str(args.candidate),
        "archive_root": str(args.archive_root),
        "guid_reference_count": len(references),
        "unique_dependency_count": len(dependencies),
        "available_count": sum(item["available"] for item in dependencies),
        "missing_count": sum(not item["available"] for item in dependencies),
        "dependencies": dependencies,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
