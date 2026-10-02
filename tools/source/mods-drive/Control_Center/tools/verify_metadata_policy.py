"""Validate the versioned safe metadata resource policy."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def verify(path: Path) -> dict:
    path = Path(path).resolve()
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        return {"valid": False, "errors": [str(exc)]}
    if data.get("schema") != "control_center.safe_metadata_resource_types.v1":
        errors.append("unsupported metadata policy schema")
    verified = data.get("verified_types", [])
    quarantined = data.get("quarantined_types", [])
    verified_names = [str(item.get("type", "")) for item in verified if isinstance(item, dict)]
    quarantined_names = [str(item.get("type", "")) for item in quarantined if isinstance(item, dict)]
    if not verified_names:
        errors.append("verified_types must not be empty")
    if len(set(verified_names)) != len(verified_names):
        errors.append("verified_types contains duplicates")
    overlap = sorted(set(verified_names) & set(quarantined_names))
    if overlap:
        errors.append("type appears in both verified and quarantined lists: " + ", ".join(overlap))
    root = path.parent.parent.resolve()
    for item in list(verified) + list(quarantined):
        evidence = str(item.get("evidence", "")).strip() if isinstance(item, dict) else ""
        if not evidence:
            errors.append("metadata entry is missing evidence")
            continue
        target = (root / evidence).resolve()
        try:
            target.relative_to(root)
        except ValueError:
            errors.append(f"evidence escapes project: {evidence}")
        else:
            if not target.is_file():
                errors.append(f"missing evidence: {evidence}")
    return {"valid": not errors, "path": str(path), "verified_count": len(verified_names), "quarantined_count": len(quarantined_names), "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("policy", type=Path)
    args = parser.parse_args()
    result = verify(args.policy)
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
