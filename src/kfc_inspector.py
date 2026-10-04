"""Offline inspector for normalized KFC3 metadata fixtures."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .analyzers import AnalysisResult, hash_inputs


def inspect_kfc_metadata(path: Path, *, analyzer_version: str = "1") -> dict[str, Any]:
    """Read normalized metadata only; do not open packages or contact the game."""
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
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
            "kind": "kfc3-metadata",
            "identity": identity,
            "build_scope": [str(resource["build"])],
            "state": "partially-verified",
            "confidence": "offline-fixture",
            "supported_claims": ["The normalized KFC3 fixture contains the recorded metadata fields."],
            "unsupported_claims": ["Offline metadata does not prove runtime registration, rendering, persistence, or compatibility."],
            "open_questions": list(resource.get("unresolved_references", [])),
            "contradictions": [],
            "evidence": [str(path)],
        })
    result = AnalysisResult("kfc-metadata-inspector", analyzer_version, hash_inputs([path]),
                            tuple(record["id"] for record in records),
                            tuple(sorted({str(item["build"]) for item in payload["resources"]})),
                            "offline-static", ("No runtime behavior is established.",), True)
    return {"analysis": result.to_dict(), "records": records}
