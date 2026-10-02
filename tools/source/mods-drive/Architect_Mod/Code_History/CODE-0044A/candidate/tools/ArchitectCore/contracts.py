"""Versioned, game-independent adapter contracts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

VALID_STATUSES = {
    "PROVEN", "PROVEN_STATIC", "PROVEN_OFFLINE", "INFERRED", "EXPERIMENTAL",
    "UNSOLVED", "DISPROVEN", "PLANNED", "SPECULATIVE",
}


def load_capability_map(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    validate_capability_map(value)
    return value


def validate_capability_map(value: dict[str, Any]) -> None:
    if not isinstance(value, dict) or value.get("schema") != "architect.vanilla_capability_map.v1":
        raise ValueError("unsupported capability-map schema")
    adapters = value.get("adapters")
    if not isinstance(adapters, list) or not adapters:
        raise ValueError("capability map requires adapters")
    adapter_ids: set[str] = set()
    capability_ids: set[str] = set()
    for adapter in adapters:
        if not isinstance(adapter, dict) or not isinstance(adapter.get("id"), str):
            raise ValueError("adapter id is required")
        if adapter["id"] in adapter_ids:
            raise ValueError(f"duplicate adapter id: {adapter['id']}")
        adapter_ids.add(adapter["id"])
        capabilities = adapter.get("capabilities", [])
        if not isinstance(capabilities, list):
            raise ValueError(f"capabilities must be a list: {adapter['id']}")
        for capability in capabilities:
            if not isinstance(capability, dict) or not isinstance(capability.get("id"), str):
                raise ValueError(f"capability id is required: {adapter['id']}")
            cid = capability["id"]
            if cid in capability_ids:
                raise ValueError(f"duplicate capability id: {cid}")
            capability_ids.add(cid)
            if capability.get("status") not in VALID_STATUSES:
                raise ValueError(f"invalid capability status: {cid}")
            for dep in capability.get("dependencies", []):
                if not isinstance(dep, str):
                    raise ValueError(f"dependency must be a string: {cid}")
                # Resolve after collecting the full set below; forward
                # references are allowed, unknown references are not.
    known_caps = capability_ids
    for adapter in adapters:
        for capability in adapter.get("capabilities", []):
            missing = set(capability.get("dependencies", [])) - known_caps
            if missing:
                raise ValueError(f"unknown capability dependency: {capability['id']}: {sorted(missing)}")
    for feature in value.get("features", []):
        if not isinstance(feature, dict) or not isinstance(feature.get("id"), str):
            raise ValueError("feature id is required")
        for dep in feature.get("requiredCapabilities", []):
            if dep not in known_caps:
                raise ValueError(f"unknown capability dependency: {feature['id']} -> {dep}")


def validate_feature_graph(value: dict[str, Any], capability_map: dict[str, Any]) -> None:
    if value.get("schema") != "architect.feature_dependency_graph.v1":
        raise ValueError("unsupported feature graph schema")
    capability_rows = {c["id"]: c for a in capability_map["adapters"] for c in a["capabilities"]}
    ids = set(capability_rows)
    features = value.get("features", [])
    feature_ids = {f.get("id") for f in features}
    if len(feature_ids) != len(features) or None in feature_ids:
        raise ValueError("duplicate or missing feature id")
    for feature in features:
        missing = set(feature.get("requiredCapabilities", [])) - ids
        if missing:
            raise ValueError(f"unknown capability reference: {feature['id']}: {sorted(missing)}")
        blocked = {c for c in feature.get("requiredCapabilities", []) if capability_rows[c].get("status") == "DISPROVEN"}
        if blocked and not feature.get("allowDisproven", False):
            raise ValueError(f"disproven capability requires explicit override: {feature['id']}: {sorted(blocked)}")
        missing_features = set(feature.get("dependsOnFeatures", [])) - feature_ids
        if missing_features:
            raise ValueError(f"unknown feature dependency: {feature['id']}: {sorted(missing_features)}")
    visiting: set[str] = set(); visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            raise ValueError(f"cyclic feature dependency at {node}")
        if node in visited:
            return
        visiting.add(node)
        feature = next(f for f in features if f["id"] == node)
        for child in feature.get("dependsOnFeatures", []):
            visit(child)
        visiting.remove(node); visited.add(node)

    for feature in features:
        visit(feature["id"])
