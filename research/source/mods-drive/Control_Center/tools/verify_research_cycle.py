"""Validate a prepared research-cycle handoff without launching the game."""
from __future__ import annotations

import argparse
import json
import hashlib
from pathlib import Path


def verify(path: Path) -> dict:
    errors: list[str] = []
    try:
        report = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        return {"schema": "control_center.research_cycle_verification.v1", "valid": False, "errors": [str(exc)]}
    if report.get("schema") != "control_center.research_cycle.v1":
        errors.append("unsupported research cycle schema")
    verified = report.get("verified_types", [])
    quarantined = report.get("quarantined_types", [])
    if not isinstance(verified, list) or not verified:
        errors.append("cycle has no verified resource types")
    if set(verified) & set(quarantined):
        errors.append("verified and quarantined resource types overlap")
    suite = Path(report.get("generated_probe_suite", ""))
    if not suite.is_absolute():
        suite = Path(path).resolve().parent / suite
    if not (suite / "mod.json").is_file():
        errors.append("generated probe suite manifest is missing")
    if not (suite / "src" / "mod.lua").is_file():
        errors.append("generated probe suite entrypoint is missing")
    if report.get("staged_probe"):
        probe = Path(report["staged_probe"])
        if not probe.is_absolute():
            probe = Path(path).resolve().parent / probe
        if not (probe / "mod.json").is_file():
            errors.append("staged probe manifest is missing")
        elif report.get("staged_probe_sha256"):
            digest = hashlib.sha256()
            for file in sorted(path for path in probe.rglob("*") if path.is_file()):
                digest.update(file.relative_to(probe).as_posix().encode())
                digest.update(file.read_bytes())
            if digest.hexdigest() != report["staged_probe_sha256"]:
                errors.append("staged probe integrity hash does not match")
    return {"schema": "control_center.research_cycle_verification.v1", "valid": not errors, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cycle", type=Path)
    args = parser.parse_args()
    result = verify(args.cycle)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
