"""Offline inspector for normalized KFC metadata fixtures.

The normalized fixture shape is an EmberVault research interchange shape; it
is not a claim that it is the native KFC3 or KFC4 file format.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .analyzers import AnalysisResult, hash_inputs, validate_offline_inputs


def inspect_kfc_metadata(path: Path, *, approved_root: Path, analyzer_version: str = "1",
                         kfc_format: str = "KFC3") -> dict[str, Any]:
    """Read normalized metadata only; do not open packages or contact the game."""
    normalized_format = str(kfc_format).upper()
    if normalized_format not in {"KFC3", "KFC4"}:
        raise ValueError("unsupported KFC format")
    validated_path = validate_offline_inputs([path], approved_root)[0]
    payload = json.loads(validated_path.read_text(encoding="utf-8-sig"))
    if payload.get("schema_version") != 1 or not isinstance(payload.get("resources"), list):
        raise ValueError("unsupported KFC metadata fixture")
    records = []
    for resource in payload["resources"]:
        required = {"id", "resource_type", "build"}
        if not required.issubset(resource):
            raise ValueError("KFC resource is missing required metadata")
        safe_id = re.sub(r"[^a-zA-Z0-9_.-]+", "-", str(resource["id"]))
        identity = {key: resource[key] for key in ("guid", "debug_name", "resource_type") if key in resource}
        records.append({
            "id": f"kfc:{resource['build']}:{resource['resource_type']}:{safe_id}",
            "kind": f"{normalized_format.lower()}-metadata",
            "identity": identity,
            "build_scope": [str(resource["build"])],
            "state": "partially-verified",
            "confidence": "offline-fixture",
            "supported_claims": [f"The normalized {normalized_format} fixture contains the recorded metadata fields."],
            "unsupported_claims": [f"The fixture does not establish the native {normalized_format} schema or runtime registration, rendering, persistence, or compatibility."],
            "open_questions": list(resource.get("unresolved_references", [])),
            "contradictions": [],
            "evidence": [str(validated_path)],
        })
    result = AnalysisResult(f"{normalized_format.lower()}-metadata-inspector", analyzer_version, hash_inputs([validated_path]),
                            tuple(record["id"] for record in records),
                            tuple(sorted({str(item["build"]) for item in payload["resources"]})),
                            "offline-static", ("No runtime behavior is established.",), True)
    return {"analysis": result.to_dict(), "records": records}
