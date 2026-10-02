"""Validate the versioned Control Center capability audit and its evidence links."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

STATES = {"verified", "experimental", "research-only", "unsupported"}


def verify(path: Path) -> dict:
    path = Path(path).resolve()
    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        return {"valid": False, "path": str(path), "errors": [str(exc)]}
    if not isinstance(data, dict) or data.get("schema") != "control_center.capability_audit.v1":
        errors.append("unsupported capability-audit schema")
    if isinstance(data, dict):
        human_report = str(data.get("human_report", "")).strip()
        if not human_report:
            errors.append("human_report is required")
        else:
            project_root = path.parent.parent.resolve()
            report_path = (project_root / human_report).resolve()
            try:
                report_path.relative_to(project_root)
            except ValueError:
                errors.append(f"human report escapes project: {human_report}")
            else:
                if not report_path.is_file():
                    errors.append(f"missing human report: {human_report}")
    capabilities = data.get("capabilities") if isinstance(data, dict) else None
    if not isinstance(capabilities, list) or not capabilities:
        errors.append("capabilities must be a non-empty array")
        capabilities = []
    phases: set[int] = set()
    ids: set[str] = set()
    for index, capability in enumerate(capabilities):
        location = f"capabilities[{index}]"
        if not isinstance(capability, dict):
            errors.append(f"{location} must be an object")
            continue
        identifier = str(capability.get("id", "")).strip()
        if not identifier:
            errors.append(f"{location}.id is required")
        elif identifier in ids:
            errors.append(f"duplicate capability id: {identifier}")
        ids.add(identifier)
        phase = capability.get("phase")
        if not isinstance(phase, int) or phase not in {1, 2, 3, 4, 5, 6}:
            errors.append(f"{location}.phase must be 1, 2, 3, 4, 5, or 6")
        else:
            phases.add(phase)
        if capability.get("state") not in STATES:
            errors.append(f"{location}.state is not a supported maturity state")
        if not str(capability.get("summary", "")).strip():
            errors.append(f"{location}.summary is required")
        if not str(capability.get("next_gate", "")).strip():
            errors.append(f"{location}.next_gate is required")
        evidence = capability.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{location}.evidence must be a non-empty array")
        else:
            for raw in evidence:
                project_root = path.parent.parent.resolve()
                evidence_path = (project_root / str(raw)).resolve()
                try:
                    evidence_path.relative_to(project_root)
                except ValueError:
                    errors.append(f"evidence path escapes project: {raw}")
                    continue
                if not evidence_path.is_file():
                    errors.append(f"missing evidence file: {raw}")
    missing_phases = sorted({1, 2, 3, 4, 5, 6} - phases)
    if missing_phases:
        errors.append("missing phase coverage: " + ", ".join(map(str, missing_phases)))
    return {
        "valid": not errors,
        "path": str(path),
        "capability_count": len(capabilities),
        "phases": sorted(phases),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audit", type=Path)
    args = parser.parse_args()
    result = verify(args.audit)
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
