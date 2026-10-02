"""Verify that the original-asset import boundary is explicitly documented."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_MARKERS = (
    "File inspection and hashing", "Dependency and ownership metadata",
    "Collision and LOD authoring", "`TemplateResource` graph access",
    "Save persistence and multiplayer authority", "Promotion rule",
    "fresh isolated session", "dependency resolution", "visible in-game use", "rollback",
)


def verify(path: Path) -> dict:
    errors: list[str] = []
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        return {"schema": "control_center.asset_import_boundary_verification.v1", "valid": False, "errors": [str(exc)]}
    for marker in REQUIRED_MARKERS:
        if marker not in text:
            errors.append(f"missing boundary section: {marker}")
    if "research-only" not in text or "quarantined" not in text:
        errors.append("report must classify research-only and quarantined paths")
    return {"schema": "control_center.asset_import_boundary_verification.v1", "valid": not errors,
            "path": str(Path(path).resolve()), "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    result = verify(parser.parse_args().report)
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
