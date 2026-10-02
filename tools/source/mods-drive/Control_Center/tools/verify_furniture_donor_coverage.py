"""Verify that the furniture-clone milestone has three distinct tracked donors."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def verify(directory: Path) -> dict[str, object]:
    errors: list[str] = []
    candidates = []
    for path in sorted(directory.glob("*_candidate.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path.name}: unreadable candidate ({exc})")
            continue
        donor = data.get("donor", {})
        donor_id = donor.get("item_id")
        if not isinstance(donor_id, int) or donor_id <= 0:
            errors.append(f"{path.name}: donor.item_id must be a positive integer")
            continue
        status = data.get("status")
        evidence_path = data.get("runtime_evidence")
        if isinstance(status, str) and "RUNTIME_REGISTRATION" in status:
            if not isinstance(evidence_path, str) or not evidence_path.strip():
                errors.append(f"{path.name}: runtime-backed candidate is missing runtime_evidence")
            elif not (directory.parents[1] / evidence_path).is_file():
                errors.append(f"{path.name}: runtime evidence file is missing: {evidence_path}")
        candidates.append({"path": str(path), "donor_item_id": donor_id, "status": status})

    donor_ids = [entry["donor_item_id"] for entry in candidates]
    if len(candidates) < 3:
        errors.append(f"three furniture candidates are required; found {len(candidates)}")
    if len(set(donor_ids)) != len(donor_ids):
        errors.append("furniture candidates must use distinct donor item IDs")
    runtime_evidence_count = sum(
        1 for entry in candidates
        if isinstance(entry.get("status"), str) and "RUNTIME_REGISTRATION" in entry["status"]
    )
    return {
        "schema": "control_center.furniture_donor_coverage_verification.v1",
        "valid": not errors,
        "candidate_count": len(candidates),
        "distinct_donor_count": len(set(donor_ids)),
        "runtime_registration_candidate_count": runtime_evidence_count,
        "candidates": candidates,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    result = verify(args.directory)
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
