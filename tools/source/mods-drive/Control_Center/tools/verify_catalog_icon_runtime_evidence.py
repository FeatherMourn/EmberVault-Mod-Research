"""Validate durable evidence for catalog-icon research results."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


SCHEMA = "control_center.catalog_icon_runtime_evidence.v1"


def validate(path: Path, root: Path | None = None) -> list[str]:
    root = (root or Path(__file__).resolve().parents[1]).resolve()
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read evidence: {exc}"]
    if data.get("schema") != SCHEMA:
        errors.append("unsupported evidence schema")
    evidence = data.get("evidence", {})
    durable = evidence.get("durable_visual_evidence")
    if not isinstance(durable, dict):
        errors.append("durable_visual_evidence is required")
        return errors
    screenshot = durable.get("catalog_tile_screenshot")
    if not isinstance(screenshot, str) or not screenshot.strip():
        errors.append("catalog tile screenshot is required")
    else:
        target = Path(screenshot)
        if not (target if target.is_absolute() else root / target).is_file():
            errors.append(f"catalog tile screenshot is missing: {screenshot}")
    if durable.get("catalog_tile_verdict") not in {"nonblank_tile_visible", "blank_tile", "not_verified"}:
        errors.append("invalid catalog tile verdict")
    if evidence.get("nonblank_catalog_tile_visible") is True and durable.get("catalog_tile_verdict") != "nonblank_tile_visible":
        errors.append("nonblank runtime claim does not match durable verdict")
    if durable.get("placed_object_verdict") not in {"placed_object_visual_verified", "not_verified"}:
        errors.append("invalid placed object verdict")
    if durable.get("save_persistence_verdict") not in {"verified", "not_verified"}:
        errors.append("invalid persistence verdict")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()
    errors = validate(args.evidence)
    result = {"schema": "control_center.catalog_icon_runtime_evidence_verification.v1", "valid": not errors, "path": str(args.evidence), "errors": errors}
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
