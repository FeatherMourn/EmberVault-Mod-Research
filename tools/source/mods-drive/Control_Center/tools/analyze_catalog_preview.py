"""Extract catalog-preview evidence from an EML JSON-lines log."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PREFIX = "[CC-BED-CLONE] "


def analyze(path: Path, start: int = 0, end: int | None = None) -> dict:
    raw = path.read_bytes()
    segment = raw[start:end]
    records: list[dict] = []
    for line in segment.splitlines():
        try:
            row = json.loads(line.decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            continue
        message = row.get("fields", {}).get("message", "")
        if isinstance(message, str) and PREFIX in message:
            records.append({"timestamp": row.get("timestamp"), "message": message})

    def latest(kind: str) -> str | None:
        marker = PREFIX + kind + "|"
        for record in reversed(records):
            message = record["message"]
            if marker in message:
                return message.split(marker, 1)[1].replace("\n", "")
        return None

    preview = {}
    for kind in ("CATALOG_PREVIEW_BEFORE", "CATALOG_PREVIEW_AFTER"):
        value = latest(kind)
        if value is not None:
            preview[kind.removeprefix("CATALOG_PREVIEW_").lower()] = dict(
                re.findall(r"(iconImage|iconModel|iconScene)=([^|]+)", value)
            )
    panic = any("panic" in record["message"].lower() for record in records)
    return {
        "schema": "control_center.catalog_preview_evidence.v1",
        "log": str(path.resolve()),
        "log_from_byte": start,
        "records": len(records),
        "preview_fields": preview,
        "ui_link": latest("UI_LINKS"),
        "ui_set_before": latest("UI_SET_BEFORE"),
        "ui_set_after": latest("UI_SET_AFTER"),
        "icon_assignment": latest("CATALOG_ICON_ASSIGNMENT"),
        "render_control": latest("CATALOG_RENDER_CONTROL"),
        "panic_observed": panic,
        "status": "evidence_found" if records else "no_probe_evidence",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--from-byte", type=int, default=0)
    parser.add_argument("--to-byte", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = analyze(args.log, args.from_byte, args.to_byte)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if result["status"] == "evidence_found" else 2


if __name__ == "__main__":
    raise SystemExit(main())
