"""Report the last confirmed phase of a localization research probe."""
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
    parser.add_argument("log", type=Path)
    parser.add_argument("--expected-key", action="append", default=[])
    parser.add_argument("--from-byte", type=int, default=0, help="ignore log bytes before a recorded session boundary")
    parser.add_argument("--output", type=Path, help="also save the structured boundary report")
    args = parser.parse_args()
    result = LocalizationDebugger().inspect(args.log, args.expected_key, from_byte=args.from_byte)
    report = {
        "schema": "control_center.localization_boundary_report.v1",
        "status": result.status,
        "build_id": result.build_id,
        "boundary": result.boundary,
        "last_marker": result.last_marker,
        "panic_observed": result.panic_observed,
        "registration": result.status == "runtime_registration_verified",
        "missing_keys": list(result.missing_keys),
        "issues": list(result.issues),
        "next_safe_action": result.next_safe_action,
        "log_sha256": result.log_sha256,
    }
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
