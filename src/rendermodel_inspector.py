"""Offline RenderModel metadata inspector."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .analyzers import AnalysisResult, hash_inputs


def inspect_rendermodel_metadata(path: Path, *, analyzer_version: str = "1") -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if payload.get("schema_version") != 1 or not isinstance(payload.get("models"), list):
        raise ValueError("unsupported RenderModel metadata fixture")
    records = []
    for model in payload["models"]:
        if not {"id", "build", "guid"}.issubset(model):
            raise ValueError("RenderModel metadata is missing required fields")
        safe_id = re.sub(r"[^a-zA-Z0-9_.-]+", "-", str(model["id"]))
        warnings = list(model.get("warnings", []))
        records.append({
            "id": f"rendermodel:{model['build']}:{safe_id}",
            "kind": "rendermodel-metadata",
            "identity": {"guid": model["guid"], "debug_name": model.get("debug_name", "")},
            "build_scope": [str(model["build"])],
            "state": "partially-verified",
            "confidence": "offline-fixture",
            "supported_claims": ["The normalized fixture records the supplied RenderModel metadata."],
            "unsupported_claims": ["Offline model metadata does not prove visual substitution, placement, persistence, or multiplayer behavior."],
            "open_questions": warnings,
            "contradictions": [],
            "evidence": [str(path)],
            "metadata": {key: model[key] for key in ("mesh_count", "material_count", "lod_count", "vertex_count", "texture_slots") if key in model},
        })
    result = AnalysisResult("rendermodel-metadata-inspector", analyzer_version, hash_inputs([path]),
                            tuple(record["id"] for record in records),
                            tuple(sorted({str(item["build"]) for item in payload["models"]})),
                            "offline-static", ("No visual or runtime behavior is established.",), True)
    return {"analysis": result.to_dict(), "records": records}
