"""Import bounded, read-only platform inventory exports into research records."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .analyzers import validate_offline_inputs


def import_platform_inventory(path: Path, *, approved_root: Path, game_build: str | None = None) -> dict[str, Any]:
    """Convert the probe TSV into bounded records without inferring behavior."""
    source = validate_offline_inputs([path], approved_root)[0]
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    lines = source.read_text(encoding="utf-8-sig").splitlines()
    if not lines or not lines[0].startswith("schema_version=1"):
        raise ValueError("unsupported platform inventory export")
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    for line in lines[1:]:
        parts = line.split("\t")
        if not parts or not parts[0]:
            continue
        if parts[0] == "error":
            errors.append("\t".join(parts[1:]))
            continue
        if parts[0] == "type" and len(parts) >= 2:
            resource_type = parts[1]
            safe = resource_type.replace("::", "_").replace("/", "_")
            records.append({
                "id": f"eml:type:{safe}",
                "kind": "eml-resource-type",
                "identity": {"resource_type": resource_type},
                "build_scope": [game_build] if game_build else [],
                "state": "partially-verified" if errors else "observed",
                "confidence": "offline-export",
                "supported_claims": ["The EML probe reported this resource type."],
                "unsupported_claims": ["Presence does not prove field semantics or runtime behavior."],
                "open_questions": [],
                "contradictions": [],
                "evidence": [str(source)],
            })
        elif parts[0] == "resource" and len(parts) >= 4:
            guid, resource_type, part_index = parts[1:4]
            records.append({
                "id": f"eml:resource:{guid}:{resource_type}:{part_index}",
                "kind": "eml-resource-observation",
                "identity": {"guid": guid, "resource_type": resource_type, "part_index": part_index},
                "build_scope": [game_build] if game_build else [],
                "state": "partially-verified" if errors else "observed",
                "confidence": "offline-export",
                "supported_claims": ["The EML probe reported this resource identity."],
                "unsupported_claims": ["Metadata does not prove resource semantics, rendering, persistence, or compatibility."],
                "open_questions": [],
                "contradictions": [],
                "evidence": [str(source)],
            })
    return {"source": str(source), "source_sha256": source_hash, "records": records, "errors": errors, "read_only": True, "runtime_approval": False}
