"""Produce a requirement-level completion snapshot without overstating readiness."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_DOCS = [
    "docs/USER_GUIDE.md", "docs/MOD_AUTHOR_GUIDE.md", "docs/EML_API_GUIDE.md",
    "docs/CLONE_AND_PATCH_GUIDE.md", "docs/VISUAL_SUBSTITUTION_GUIDE.md",
    "docs/TUNING_GUIDE.md", "docs/BUILDER_GUIDE.md", "docs/RESEARCH_PROBE_GUIDE.md",
    "docs/RECOVERY_GUIDE.md", "docs/UPDATE_MIGRATION_GUIDE.md",
    "docs/SECURITY_AND_SAFETY_POLICY.md", "docs/TROUBLESHOOTING_GUIDE.md",
]
ALLOWED_STATES = {"verified", "experimental", "research-only", "unsupported", "disabled"}


def audit(root: Path, capability_path: Path, live_snapshot: dict | None = None,
          milestone_snapshot: dict | None = None) -> dict:
    root = Path(root).resolve()
    errors: list[str] = []
    capability = json.loads(Path(capability_path).read_text(encoding="utf-8-sig"))
    if capability.get("schema") != "control_center.capability_audit.v1":
        errors.append("capability audit schema is unsupported")
    capabilities = capability.get("capabilities", [])
    states = {str(item.get("state")) for item in capabilities if isinstance(item, dict)}
    for index, item in enumerate(capabilities if isinstance(capabilities, list) else []):
        if not isinstance(item, dict) or not str(item.get("id", "")).strip():
            errors.append(f"capability {index} is missing an id")
        if not isinstance(item, dict) or item.get("state") not in ALLOWED_STATES:
            errors.append(f"capability {index} has an invalid state")
    missing_docs = [path for path in REQUIRED_DOCS if not (root / path).is_file()]
    if missing_docs:
        errors.extend(f"missing required document: {path}" for path in missing_docs)
    if not isinstance(capabilities, list) or not capabilities:
        errors.append("capability audit contains no capabilities")
    unresolved = [item.get("id") for item in capabilities if item.get("state") in {"research-only", "unsupported"}]
    for item in capabilities:
        if isinstance(item, dict) and item.get("state") in {"research-only", "unsupported"}:
            if not isinstance(item.get("evidence"), list) or not item["evidence"]:
                errors.append(f"unresolved capability lacks evidence: {item.get('id')}")
            if not str(item.get("next_gate", "")).strip():
                errors.append(f"unresolved capability lacks next gate: {item.get('id')}")
            for evidence in item.get("evidence", []) if isinstance(item.get("evidence"), list) else []:
                evidence_path = Path(str(evidence))
                if not (evidence_path if evidence_path.is_absolute() else root / evidence_path).is_file():
                    errors.append(f"missing capability evidence: {item.get('id')} -> {evidence}")
    if live_snapshot and not live_snapshot.get("isolation_ready", False):
        errors.append("stable live profile is not isolated")
    if milestone_snapshot is not None:
        if milestone_snapshot.get("schema") != "control_center.milestone_verification.v1":
            errors.append("milestone verification schema is unsupported")
        elif milestone_snapshot.get("passed") is not True:
            errors.append("current milestone verification has failing gates")
    return {
        "schema": "control_center.completion_audit.v1",
        "valid": not errors,
        "project_complete": not errors and not unresolved,
        "capability_count": len(capabilities),
        "states": {state: sum(1 for item in capabilities if item.get("state") == state) for state in sorted(states)},
        "unresolved_capabilities": unresolved,
        "missing_documents": missing_docs,
        "milestone_passed": None if milestone_snapshot is None else milestone_snapshot.get("passed") is True,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--capability-audit", type=Path)
    parser.add_argument("--live-snapshot", type=Path)
    parser.add_argument("--milestone", type=Path)
    parser.add_argument("--no-milestone", action="store_true",
                        help="skip milestone snapshot validation when called by the milestone runner")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    capability = args.capability_audit or root / "research" / "CAPABILITY_AUDIT_20260927.json"
    live = json.loads(args.live_snapshot.read_text(encoding="utf-8")) if args.live_snapshot else None
    if args.no_milestone:
        milestone_path = None
    elif args.milestone:
        milestone_path = args.milestone
    else:
        candidates = [path for path in (root / "research").glob("MILESTONE_*.json") if path.is_file()]
        milestone_path = max(candidates, key=lambda path: path.stat().st_mtime) if candidates else root / "research" / "MILESTONE_VERIFICATION_20260928.json"
    milestone = json.loads(milestone_path.read_text(encoding="utf-8")) if milestone_path and milestone_path.is_file() else None
    result = audit(root, capability, live, milestone)
    rendered = json.dumps(result, indent=2) + "\n"
    print(rendered, end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
