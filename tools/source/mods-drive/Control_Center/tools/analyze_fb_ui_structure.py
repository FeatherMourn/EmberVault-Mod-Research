"""Extract read-only FbUiBundle structure markers from an EML log."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PREFIX = "[CC-FBUI-STRUCTURE] "


def analyze(path: Path, start: int = 0) -> dict:
    records = []
    for line in path.read_bytes()[start:].splitlines():
        try:
            row = json.loads(line.decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            continue
        message = row.get("fields", {}).get("message", "")
        if isinstance(message, str) and message.startswith(PREFIX):
            records.append(message[len(PREFIX):].replace("\n", ""))
    fields = {}
    bundles = None
    warning = None
    for record in records:
        kind, _, value = record.partition("|")
        if kind == "FIELD":
            name, _, detail = value.partition("|")
            fields[name] = {
                "raw": detail,
                "lua_type": re.search(r"lua_type=([^|]+)", detail).group(1) if re.search(r"lua_type=([^|]+)", detail) else None,
                "count": int(re.search(r"count=(\d+)", detail).group(1)) if re.search(r"count=(\d+)", detail) else None,
            }
        elif kind == "BUNDLES":
            bundles = int(value)
        elif kind == "WARNING":
            warning = value
    return {
        "schema": "control_center.fb_ui_bundle_structure_evidence.v1",
        "log": str(path.resolve()),
        "log_from_byte": start,
        "records": len(records),
        "bundles": bundles,
        "fields": fields,
        "warning": warning,
        "read_only": warning == "read_only_structure_only",
        "status": "evidence_found" if records else "no_probe_evidence",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--from-byte", type=int, default=0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = analyze(args.log, args.from_byte)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["status"] == "evidence_found" else 2


if __name__ == "__main__":
    raise SystemExit(main())
