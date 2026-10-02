"""Prepare a reproducible, safety-gated research cycle without launching the game."""
from __future__ import annotations

import argparse
import contextlib
import json
import io
import sys
import shutil
import hashlib
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_metadata_probe_suite import main as build_suite_main
from verify_live_loader import inspect
from verify_research_cycle import verify


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("policy", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--game-dir", type=Path)
    parser.add_argument("--expected-build")
    parser.add_argument("--probe", type=Path,
                        help="copy one staged probe into the cycle for an auditable handoff")
    args = parser.parse_args()

    policy = json.loads(args.policy.read_text(encoding="utf-8-sig"))
    if policy.get("schema") != "control_center.safe_metadata_resource_types.v1":
        raise SystemExit("Unsupported metadata policy schema.")
    verified = [str(item["type"]) for item in policy.get("verified_types", [])]
    quarantined = [str(item["type"]) for item in policy.get("quarantined_types", [])]
    if not verified:
        raise SystemExit("Metadata policy contains no verified resource types.")

    args.output.mkdir(parents=True, exist_ok=False)
    suite = args.output / "metadata_probe_suite"
    sys.argv = ["build_metadata_probe_suite", str(args.policy), str(suite)]
    with contextlib.redirect_stdout(io.StringIO()):
        build_suite_main()

    probe_path = None
    probe_hash = None
    if args.probe:
        source = args.probe.resolve()
        if not source.is_dir() or not (source / "mod.json").is_file():
            raise SystemExit("Probe must be a directory containing mod.json.")
        probe_path = args.output / "staged_probe"
        shutil.copytree(source, probe_path)
        digest = hashlib.sha256()
        for file in sorted(path for path in probe_path.rglob("*") if path.is_file()):
            digest.update(file.relative_to(probe_path).as_posix().encode())
            digest.update(file.read_bytes())
        probe_hash = digest.hexdigest()

    preflight = None
    if args.game_dir:
        preflight = inspect(args.game_dir, expected_build=args.expected_build)

    report = {
        "schema": "control_center.research_cycle.v1",
        "created": datetime.now(timezone.utc).isoformat(),
        "policy": str(args.policy.resolve()),
        "target_build": policy.get("target_build"),
        "verified_types": verified,
        "quarantined_types": quarantined,
        "generated_probe_suite": "metadata_probe_suite",
        "staged_probe": "staged_probe" if probe_path else None,
        "staged_probe_sha256": probe_hash,
        "live_preflight": preflight,
        "launch_required": True,
        "next_action": "Run the generated research-only probe in an isolated profile, then verify its session evidence.",
    }
    cycle_path = args.output / "RESEARCH_CYCLE.json"
    cycle_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    validation = verify(cycle_path)
    if not validation["valid"]:
        raise SystemExit("Generated research cycle failed validation: " + "; ".join(validation["errors"]))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
