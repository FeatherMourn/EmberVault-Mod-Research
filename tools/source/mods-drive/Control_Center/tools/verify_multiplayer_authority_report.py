"""Verify the required conservative multiplayer-authority boundary report."""
from __future__ import annotations
import argparse, json
from pathlib import Path

REQUIRED_PHRASES = (
    "Server-owned item definitions",
    "Replication of custom resources",
    "Save persistence across peers",
    "Permissions/ownership",
    "Dedicated-server loading",
    "Anti-cheat and trust boundary",
    "client-only",
    "multiplayer-safe",
    "peer-visible evidence",
    "remains unsupported",
)

def validate(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        return [f"cannot read report: {exc}"]
    errors = [f"missing required boundary statement: {phrase}" for phrase in REQUIRED_PHRASES if phrase.casefold() not in text.casefold()]
    if "## Findings" not in text or "## Safe product policy" not in text or "## Conclusion" not in text:
        errors.append("report must contain Findings, Safe product policy, and Conclusion sections")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    errors = validate(args.report)
    print(json.dumps({"schema": "control_center.multiplayer_authority_report_verification.v1", "valid": not errors, "errors": errors}, indent=2))
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
