"""Queries over offline capability/dependency artifacts."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .contracts import load_capability_map, validate_feature_graph


class ArchitectCoreQuery:
    def __init__(self, capability_map: dict[str, Any], feature_graph: dict[str, Any] | None = None):
        self.capability_map = capability_map
        self.feature_graph = feature_graph
        if feature_graph is not None:
            validate_feature_graph(feature_graph, capability_map)

    @classmethod
    def from_files(cls, capability_map_path: str | Path, feature_graph_path: str | Path | None = None) -> "ArchitectCoreQuery":
        import json
        graph = None
        if feature_graph_path:
            graph = json.loads(Path(feature_graph_path).read_text(encoding="utf-8-sig"))
        return cls(load_capability_map(capability_map_path), graph)

    def capabilities(self, status: str | None = None) -> list[dict[str, Any]]:
        rows = [c | {"adapter": a["id"]} for a in self.capability_map["adapters"] for c in a["capabilities"]]
        return [c for c in rows if status is None or c["status"] == status]

    def proven(self) -> list[dict[str, Any]]:
        return [c for c in self.capabilities() if c["status"] in {"PROVEN", "PROVEN_STATIC", "PROVEN_OFFLINE"}]

    def safe_read_only_milestones(self) -> list[dict[str, Any]]:
        return [c for c in self.capabilities() if c.get("runtime", {}).get("runtime_read") in {"PROVEN", "PLANNED"} and c.get("risk") in {"LOW", "MEDIUM"}]

    def features_blocked_by(self, capability_id: str) -> list[dict[str, Any]]:
        if not self.feature_graph:
            return []
        return [f for f in self.feature_graph.get("features", []) if capability_id in f.get("requiredCapabilities", [])]

    def next_candidates(self) -> list[dict[str, Any]]:
        if not self.feature_graph:
            return []
        return sorted(self.feature_graph.get("features", []), key=lambda f: (f.get("priority", 999), f["id"]))
