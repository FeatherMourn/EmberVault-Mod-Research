"""Verify isolated Hunter NPC animation-graph attachment evidence."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

SCHEMA = "control_center.animation_graph_attachment_evidence_verification.v1"
DONOR = "0022fed6-0380-4125-be31-ba8b5fdcbfcd"
CLONE = "7d3109de-80a7-44ad-a549-680460153d46"

def verify(path: Path, expected_build: str, expected_api: str) -> dict:
    errors: list[str] = []
    try: data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc: return {"schema": SCHEMA, "valid": False, "errors": [str(exc)]}
    if data.get("schema") != "control_center.animation_graph_npc_attachment_runtime_evidence.v1": errors.append("unsupported evidence schema")
    if data.get("game_build") != expected_build: errors.append("game build mismatch")
    if data.get("loader_api_version") != expected_api: errors.append("loader API mismatch")
    graph = data.get("graph", {})
    expected_graph = {"type": "keen::anim_graph::runtime_graph::AnimationGraphResource2_0", "donor_guid": DONOR, "clone_guid": CLONE, "clone_nodes": 108, "donor_preserved": True}
    if graph != expected_graph: errors.append("graph identity or preservation mismatch")
    attachment = data.get("attachment", {})
    expected_attachment = {"owner_type": "keen::NpcCollection", "owner_guid": "377f61dc-c7b8-4e4f-830f-7d2c3e8b7fd8", "owner_entry": "NPC_Workshop_Hunter01", "field": "uiRendering.animationGraph2", "before": DONOR, "after": CLONE, "verified": True}
    if attachment != expected_attachment: errors.append("owner attachment mismatch")
    if data.get("prohibited_boundaries") != {"template": False, "entity": False, "world": False, "save": False}: errors.append("prohibited boundary was crossed")
    if data.get("result") != "animation_graph_npc_attachment_complete": errors.append("completion marker is missing")
    if data.get("current_session_errors") != []: errors.append("current session contains errors")
    for field in ("game_stopped", "probe_uninstalled", "stable_profile_restored", "isolation_ready"):
        if data.get("cleanup", {}).get(field) is not True: errors.append(f"cleanup {field} is not verified")
    if not data.get("limitations"): errors.append("limitations must remain documented")
    return {"schema": SCHEMA, "valid": not errors, "state": "research-only", "promotion_ready": False, "owner_attachment_verified": not errors, "errors": errors}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("evidence", type=Path); parser.add_argument("--expected-build", required=True); parser.add_argument("--expected-api", required=True)
    args = parser.parse_args(); result = verify(args.evidence, args.expected_build, args.expected_api); print(json.dumps(result, indent=2, sort_keys=True)); return 0 if result["valid"] else 1

if __name__ == "__main__": raise SystemExit(main())
