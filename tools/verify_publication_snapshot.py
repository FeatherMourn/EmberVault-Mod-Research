"""Verify that the committed public snapshot is reproducible from the catalog."""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.publication import build_web_publication_from_catalog


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=Path("research/catalog.sqlite"))
    parser.add_argument("--snapshot", type=Path, default=Path("research/publication/web-catalog-publication-20261004.json"))
    args = parser.parse_args()
    expected = json.loads(args.snapshot.read_text(encoding="utf-8"))
    generated = build_web_publication_from_catalog(
        args.catalog,
        reviewed_ids={record["id"] for record in expected["records"]},
        generated_at=expected["generated_at"],
    )
    if generated != expected:
        raise SystemExit("committed publication snapshot is not reproducible")
    print(f"publication snapshot reproducible: {len(expected['records'])} records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
