"""Verify a persisted localization boundary report without promoting it."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.localization_debug import LocalizationDebugger


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    try:
        report = json.loads(args.report.read_text(encoding="utf-8-sig"))
        errors = list(LocalizationDebugger.validate_report(report))
    except (OSError, ValueError, TypeError) as exc:
        errors = [str(exc)]
    result = {"schema": "control_center.localization_boundary_verification.v1", "valid": not errors, "errors": errors}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
