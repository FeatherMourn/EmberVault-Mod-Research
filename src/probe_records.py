"""Validation for read-only EML/KFC4 probe manifests and evidence exports."""
from __future__ import annotations

from typing import Any


EVIDENCE_STATES = {"observed", "partial", "blocked", "unsupported", "unverified"}
REQUIRED_FIELDS = {
    "probe_id", "probe_version", "game_build", "eml_version", "started_at",
    "completed_at", "input_hashes", "output_hashes", "evidence_state",
    "limitations", "errors",
}


def validate_probe_record(record: dict[str, Any]) -> dict[str, Any]:
    """Validate one probe result without executing or importing probe code."""
    missing = sorted(REQUIRED_FIELDS - set(record))
    if missing:
        raise ValueError(f"probe record missing required fields: {', '.join(missing)}")
    if record.get("evidence_state") not in EVIDENCE_STATES:
        raise ValueError("unsupported probe evidence state")
    for field in ("input_hashes", "output_hashes", "limitations", "errors"):
        if not isinstance(record[field], list):
            raise ValueError(f"probe field must be a list: {field}")
    if not record["input_hashes"] or not record["output_hashes"]:
        raise ValueError("probe records must declare input and output hashes")
    if not record["limitations"]:
        raise ValueError("probe records must declare limitations")
    if record.get("read_only") is not True or record.get("runtime_approval") is not False:
        raise ValueError("probe records must remain read-only and unapproved for runtime")
    return {"valid": True, "probe_id": record["probe_id"], "evidence_state": record["evidence_state"], "read_only": True}


def validate_probe_collection(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate a collection export and return a deterministic summary."""
    if payload.get("schema_version") != 1 or payload.get("read_only") is not True:
        raise ValueError("unsupported or non-read-only probe collection")
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError("probe collection records must be a list")
    validated = [validate_probe_record(record) for record in records]
    return {
        "schema_version": 1,
        "valid": True,
        "read_only": True,
        "runtime_approval": False,
        "count": len(validated),
        "by_state": {state: sum(item["evidence_state"] == state for item in validated) for state in sorted(EVIDENCE_STATES)},
    }
