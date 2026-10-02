"""Offline reflection candidate ranking for the Target Resolver milestone.

This module only reads the exported ``types.json`` metadata.  It deliberately
does not attach to Enshrouded, inspect process memory, or assign game
semantics to a reflected type.  Scores are triage hints for later static
analysis, not proof of a target/raycast implementation.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

BUILD = 1076226
TERMS = (
    "target", "interact", "interaction", "hover", "focus", "aim", "ray",
    "hit", "cursor", "trace", "pick", "select", "crosshair", "placement",
    "building", "terrain", "camera", "entity", "distance", "normal",
    "origin", "direction", "position", "surface", "material",
)
VECTOR_HINTS = ("vec", "float3", "float4", "vector", "transform", "quat", "position")
ENTITY_HINTS = ("entity", "objectid", "object_id", "guid", "netid", "network")


def _field_rows(t: dict[str, Any], types_by_index: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, field in (t.get("structFields") or {}).items():
        if not isinstance(field, dict):
            continue
        type_id = field.get("type")
        target = types_by_index.get(type_id, {}) if isinstance(type_id, int) else {}
        rows.append({
            "name": name,
            "offset": field.get("dataOffset"),
            "typeIndex": type_id,
            "typeName": target.get("qualifiedName") or target.get("name"),
            "attributes": sorted((field.get("attributes") or {}).keys()),
        })
    return sorted(rows, key=lambda x: (x["offset"] is None, x["offset"] or 0, x["name"]))


def rank_reflection_candidates(types_path: str | Path, max_candidates: int = 80) -> dict[str, Any]:
    source = Path(types_path)
    document = json.loads(source.read_text(encoding="utf-8-sig"))
    types = document.get("types") if isinstance(document, dict) else None
    if not isinstance(types, list):
        raise ValueError("types.json does not contain a types list")
    by_index = {int(t["index"]): t for t in types if isinstance(t, dict) and isinstance(t.get("index"), int)}
    ranked: list[dict[str, Any]] = []
    for t in types:
        if not isinstance(t, dict) or not t.get("structFields"):
            continue
        qname = str(t.get("qualifiedName") or "")
        fields = _field_rows(t, by_index)
        haystack = (qname + " " + " ".join(f["name"] for f in fields)).lower()
        reasons: list[str] = []
        score = 0
        for term in TERMS:
            in_type = re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", qname.lower()) is not None
            in_field = any(term in f["name"].lower() for f in fields)
            if in_type:
                score += 3; reasons.append(f"type-term:{term}")
            elif in_field:
                score += 2; reasons.append(f"field-term:{term}")
        vector_fields = [f["name"] for f in fields if any(h in str(f.get("typeName") or "").lower() or h in f["name"].lower() for h in VECTOR_HINTS)]
        entity_fields = [f["name"] for f in fields if any(h in str(f.get("typeName") or "").lower() or h in f["name"].lower() for h in ENTITY_HINTS)]
        if vector_fields:
            score += 2; reasons.append("vector/transform-shaped field")
        if entity_fields:
            score += 2; reasons.append("entity/object identity-shaped field")
        if any(k in haystack for k in ("distance", "fraction", "normal", "surface")):
            score += 2; reasons.append("hit-result-shaped scalar")
        if isinstance(t.get("size"), int) and 0 < t["size"] <= 512:
            score += 1; reasons.append("bounded struct size")
        if score < 4:
            continue
        ranked.append({
            "qualifiedName": qname,
            "name": t.get("name"),
            "typeIndex": t.get("index"),
            "size": t.get("size"),
            "alignment": t.get("alignment"),
            "primitiveType": t.get("primitiveType"),
            "score": score,
            "reasons": reasons[:12],
            "fields": fields,
            "vectorOrTransformFields": vector_fields,
            "entityIdentityFields": entity_fields,
            "status": "PROVEN_STATIC_REFLECTION_CANDIDATE",
            "semanticStatus": "UNSOLVED",
        })
    ranked.sort(key=lambda row: (-row["score"], row["qualifiedName"]))
    # Keep a small set of high-value reflected controls even if their names do
    # not meet the heuristic threshold.  Their presence is metadata evidence,
    # not proof that they are wired to a callable target observer.
    control_names = (
        "keen::ecs::ClientCursor", "keen::ecs::ClientCursorInput",
        "keen::ecs::CursorSelectObjectAction", "keen::ecs::PlayerFocus",
        "keen::ecs::ClientPlayerFocus", "keen::ecs::DebugHitResult",
        "keen::ecs::TargetEntity", "keen::ecs::TargetPosition",
        "keen::ecs::InteractionQuery", "keen::ecs::ClientInteractionQuery",
    )
    by_name = {row["qualifiedName"]: row for row in ranked}
    controls: list[dict[str, Any]] = []
    for name in control_names:
        t = next((x for x in types if isinstance(x, dict) and x.get("qualifiedName") == name), None)
        if t is None:
            continue
        row = by_name.get(name)
        if row is None:
            row = {
                "qualifiedName": name, "name": t.get("name"), "typeIndex": t.get("index"),
                "size": t.get("size"), "alignment": t.get("alignment"),
                "primitiveType": t.get("primitiveType"), "score": 0,
                "reasons": ["explicit control-type inclusion"],
                "fields": _field_rows(t, by_index),
                "vectorOrTransformFields": [], "entityIdentityFields": [],
                "status": "PROVEN_STATIC_REFLECTION_CANDIDATE", "semanticStatus": "UNSOLVED",
            }
        controls.append(row)
    return {
        "schema": "architect.target_resolver_reflection_candidates.v1",
        "gameBuild": BUILD,
        "analysisMode": "offline_static_reflection_only",
        "source": str(source),
        "sourceVersion": document.get("version"),
        "searchTerms": list(TERMS),
        "candidateCountBeforeCap": len(ranked),
        "candidates": ranked[:max_candidates],
        "controlCandidates": controls,
        "safety": {
            "processAccess": False,
            "memoryRead": False,
            "memoryWrite": False,
            "hooksInstalled": False,
            "semanticClaims": False,
        },
        "interpretation": "Scores rank reflected shapes for manual disassembly; they do not prove target acquisition, ray casting, hover state, or a callable observer.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--types", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-candidates", type=int, default=80)
    args = parser.parse_args()
    result = rank_reflection_candidates(args.types, max(1, args.max_candidates))
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"candidates={len(result['candidates'])} total={result['candidateCountBeforeCap']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
