"""Offline KFC comparison tool for Enshrouded resource-registration research.

This deliberately does not write game archives. It records the KFC3 header,
compares archive fingerprints, and verifies whether a candidate descriptor
survived an unpack/repack cycle.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def archive_info(path: Path) -> dict:
    raw = path.read_bytes()
    return {
        "path": str(path),
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "magic": raw[:4].decode("ascii", errors="replace"),
        "version_bytes": raw[:8].hex(" "),
        "header_prefix": raw[:128].hex(" "),
    }


def extracted_summary(root: Path, needle: str | None) -> dict:
    files = [p for p in root.rglob("*.json") if p.is_file()]
    matches = []
    if needle:
        for path in files:
            try:
                text = path.read_text(encoding="utf-8-sig")
            except UnicodeDecodeError:
                continue
            if needle in text:
                matches.append(str(path))
    return {"json_descriptors": len(files), "needle": needle, "matches": matches}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, action="append", required=True)
    parser.add_argument("--extracted", type=Path, action="append", default=[])
    parser.add_argument("--needle")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = {
        "tool": "kfc_index_inspector",
        "archives": [archive_info(path) for path in args.archive],
        "extracted": [
            {"path": str(root), **extracted_summary(root, args.needle)}
            for root in args.extracted
        ],
    }
    rendered = json.dumps(report, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
