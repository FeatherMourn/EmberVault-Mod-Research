"""Verify localization probe records do not overclaim UI promotion."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.localization import LocalizationService


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalog", type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(args.catalog.read_text(encoding="utf-8-sig"))
        entries = payload.get("entries") if isinstance(payload, dict) else None
        errors: list[str] = []
        if not isinstance(entries, list) or not entries:
            errors.append("localization catalog must contain at least one entry")
        else:
            for index, entry in enumerate(entries):
                errors.extend(f"entry {index}: {issue}" for issue in LocalizationService.validate_runtime_evidence(entry))
        result = {"schema": "control_center.localization_evidence_verification.v1", "valid": not errors, "errors": errors}
    except (OSError, ValueError, TypeError) as exc:
        result = {"schema": "control_center.localization_evidence_verification.v1", "valid": False, "errors": [str(exc)]}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
