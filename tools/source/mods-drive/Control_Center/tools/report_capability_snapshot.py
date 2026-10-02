"""Render one current capability and platform-health snapshot."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}


def latest_research_file(root: Path, pattern: str, fallback: str) -> Path:
    """Use the newest generated evidence while preserving a stable fallback."""
    research = root / "research"
    candidates = sorted(
        research.glob(pattern),
        key=lambda path: path.stat().st_mtime if path.is_file() else 0,
        reverse=True,
    )
    return candidates[0] if candidates else research / fallback


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path)
    parser.add_argument("--gate", type=Path)
    parser.add_argument("--preflight", type=Path)
    parser.add_argument("--metadata-policy", type=Path)
    parser.add_argument("--test-count", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = Path.cwd()
    args.audit = args.audit or latest_research_file(root, "CAPABILITY_AUDIT_*.json", "CAPABILITY_AUDIT_20260927.json")
    args.gate = args.gate or latest_research_file(root, "MILESTONE_QUALITY_GATE_*.json", "MILESTONE_QUALITY_GATE_20260928.json")
    args.preflight = args.preflight or latest_research_file(root, "live_preflight_*.json", "live_preflight_after_iteminfo_metadata_20260928.json")
    args.metadata_policy = args.metadata_policy or latest_research_file(root, "SAFE_METADATA_RESOURCE_TYPES_*.json", "SAFE_METADATA_RESOURCE_TYPES_20260928.json")
    audit, gate, preflight, metadata = load(args.audit), load(args.gate), load(args.preflight), load(args.metadata_policy)
    capabilities = audit.get("capabilities", [])
    snapshot = {
        "schema": "control_center.capability_snapshot.v1",
        "generated": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "capability_audit": str(args.audit),
            "milestone_gate": str(args.gate),
            "live_preflight": str(args.preflight),
            "metadata_policy": str(args.metadata_policy),
        },
        "target_build": audit.get("target_build"),
        "release_baseline": "1.0.2",
        "milestone_passed": bool(gate.get("passed")),
        "test_count": args.test_count if args.test_count is not None else next((
            int(part.split(" tests", 1)[0].split()[-1])
            for gate_item in gate.get("gates", [])
            if gate_item.get("name") == "tests"
            for part in str(gate_item.get("stderr_tail", "")).splitlines()
            if part.startswith("Ran ") and " tests" in part
        ), None),
        "capability_counts": {
            state: sum(1 for item in capabilities if item.get("state") == state)
            for state in ("verified", "experimental", "research-only", "unsupported")
        },
        "capabilities": [
            {"id": item.get("id"), "phase": item.get("phase"), "state": item.get("state")}
            for item in capabilities
        ],
        "live_preflight": {
            "status": preflight.get("status"),
            "isolation_ready": preflight.get("isolation_ready"),
            "game_build": preflight.get("game_build"),
            "warnings": preflight.get("warnings", []),
        },
        "metadata_policy": {
            "verified_types": [item.get("type") for item in metadata.get("verified_types", [])],
            "observed_counts": {item.get("type"): item.get("observed_count") for item in metadata.get("verified_types", [])},
            "quarantined_types": [item.get("type") for item in metadata.get("quarantined_types", [])],
            "target_build": metadata.get("target_build"),
        },
    }
    live_build = snapshot["live_preflight"]["game_build"]
    policy_build = snapshot["metadata_policy"]["target_build"]
    snapshot["metadata_policy"]["compatible"] = bool(live_build and policy_build and live_build == policy_build)
    rendered = json.dumps(snapshot, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    # The snapshot is itself one of the milestone inputs, so do not require
    # the previous milestone file to already report true while regenerating it.
    return 0 if snapshot["live_preflight"]["isolation_ready"] and snapshot["metadata_policy"]["compatible"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
