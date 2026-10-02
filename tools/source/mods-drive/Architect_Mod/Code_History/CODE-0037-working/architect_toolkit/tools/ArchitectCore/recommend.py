"""Generate a conservative next-capability recommendation from the graph."""
from __future__ import annotations

import json
from pathlib import Path

from .contracts import load_capability_map, validate_feature_graph


def build_recommendation(capability_path: str | Path, graph_path: str | Path) -> dict:
    capability_map = load_capability_map(capability_path)
    graph = json.loads(Path(graph_path).read_text(encoding="utf-8-sig"))
    validate_feature_graph(graph, capability_map)
    proven = {c["id"] for a in capability_map["adapters"] for c in a["capabilities"] if c["status"] in {"PROVEN", "PROVEN_STATIC", "PROVEN_OFFLINE"}}
    candidates = []
    for feature in sorted(graph["features"], key=lambda f: (f.get("priority", 999), f["id"])):
        required = feature.get("requiredCapabilities", [])
        unresolved = [c for c in required if c not in proven]
        candidates.append({"featureId": feature["id"], "requiredCapabilities": required,
                           "status": feature.get("status"), "priority": feature.get("priority"),
                           "readyPrerequisites": len(required) - len(unresolved),
                           "unresolvedPrerequisites": unresolved, "risk": feature.get("risk"),
                           "rationale": feature.get("smallestProofMilestone")})
    return {"schema":"architect.next_capability_recommendation.v1",
            "selectionMode":"dependency_and_evidence_based", "gameBuild":1076226,
            "candidates":candidates[:8], "recommendedOrder":[c["featureId"] for c in candidates[:5]],
            "blockedByDisproven":["trackingItemId helper mutation as geometry authority"],
            "policy":"Do not select a mutation milestone while shared read-only prerequisites remain unresolved."}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument("--capability-map", required=True); parser.add_argument("--graph", required=True); parser.add_argument("--output", required=True)
    args = parser.parse_args(); Path(args.output).write_text(json.dumps(build_recommendation(args.capability_map, args.graph), indent=2) + "\n", encoding="utf-8")
