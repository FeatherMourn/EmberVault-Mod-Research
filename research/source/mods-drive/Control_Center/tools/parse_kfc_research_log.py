"""Parse a Control Center KFC probe log into a compact research result."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "research" / "kfc_probe_results_1076226.json"


def parse(path: Path) -> dict:
    rows: dict[str, dict] = defaultdict(lambda: {"readable": False, "resource_loaded": False, "samples": []})
    build = None
    entries = 0
    errors = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            continue
        message = str(event.get("fields", {}).get("message", ""))
        marker = "[CC-RESEARCH] "
        if marker not in message:
            continue
        payload = message.split(marker, 1)[1]
        entries += 1
        if payload.startswith("BEGIN|build="):
            build = payload.split("=", 1)[1]
            continue
        if payload.startswith("END|build="):
            build = build or payload.split("=", 1)[1]
            continue
        parts = payload.split("|", 4)
        if not parts:
            continue
        candidate = parts[0]
        row = rows[candidate]
        if len(parts) >= 2 and parts[1] == "readable":
            row["readable"] = True
            row["resource_loaded"] = True
            row["instances"] = max(int(row.get("instances", 0)), int(parts[2]))
            if len(parts) >= 5 and len(row["samples"]) < 3:
                row["samples"].append({"type": parts[3], "value": parts[4][:500]})
        elif len(parts) >= 2 and parts[1] == "resource_not_loaded":
            row["resource_loaded"] = False
        elif len(parts) >= 2 and parts[1] in {"field_error", "resource_call_error"}:
            row["errors"].append("|".join(parts[1:]))
            errors.append(payload)
    readable = sum(1 for row in rows.values() if row["readable"])
    not_loaded = sum(1 for row in rows.values() if not row["resource_loaded"] and not row.get("errors"))
    return {
        "schema": "control_center.kfc_probe_results.v1",
        "build": build or "unknown",
        "log": str(path),
        "entries": entries,
        "readable_resource_fields": readable,
        "not_loaded_resource_fields": not_loaded,
        "error_count": len(errors),
        "status": "readback_complete" if entries and not errors else "review_required",
        "results": dict(sorted(rows.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    result = parse(args.log)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Parsed {result['entries']} probe entries")
    print(f"Readable: {result['readable_resource_fields']}; not loaded: {result['not_loaded_resource_fields']}; errors: {result['error_count']}")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
