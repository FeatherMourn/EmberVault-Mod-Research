"""Validate a Research Lab screenshot sidecar without claiming visual success."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SCHEMA = "control_center.game_screenshot.v1"
KINDS = {"catalog", "item_info", "recipe", "placed_item", "localization", "gameplay", "other"}


def verify(report_path: Path) -> dict[str, object]:
    errors: list[str] = []
    try:
        data = json.loads(Path(report_path).read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"schema": "control_center.game_screenshot_evidence_verification.v1", "valid": False, "errors": [str(exc)]}
    if data.get("schema") != SCHEMA:
        errors.append("unsupported screenshot report schema")
    kind = data.get("evidence_kind")
    if kind not in KINDS:
        errors.append("evidence_kind must be one of the supported capture categories")
    image = data.get("path")
    image_path = Path(image) if isinstance(image, str) else None
    if image_path is None or not image_path.is_file():
        errors.append("screenshot path is missing or does not exist")
    elif image_path.stat().st_size <= 0:
        errors.append("screenshot file is empty")
    if not isinstance(data.get("captured_utc"), str) or not data["captured_utc"].strip():
        errors.append("captured_utc is required")
    return {
        "schema": "control_center.game_screenshot_evidence_verification.v1",
        "valid": not errors,
        "evidence_kind": kind,
        "path": str(image_path) if image_path else None,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    result = verify(args.report)
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
