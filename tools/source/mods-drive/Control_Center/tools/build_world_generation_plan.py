"""Generate a pinned, research-only world-generation plan skeleton."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def build(build: str, scene_guid: str, name: str) -> dict:
    return {
        "schema": "control_center.world_generation_plan.v1",
        "feature_state": "research-only",
        "name": name,
        "game_build": build,
        "donor_scene_guid": scene_guid,
        "layers": [
            {"resource_type": "keen::VoxelWorldResource", "part": 0, "intent": "preview-only"},
            {"resource_type": "keen::FogVoxelMappingResource", "part": 0, "intent": "preview-only"}
        ],
        "operations": [
            {"kind": "map-layer", "layer": "solid", "approved": False},
            {"kind": "preview-bounds", "layer": "fog-mapping", "approved": False}
        ],
        "prohibited_actions": ["read-voxel-content", "write-live-world", "register-resource", "attach-resource", "write-save", "multiplayer-use"],
        "promotion": {"runtime_payload_read": False, "authoring_verified": False, "save_verified": False, "multiplayer_verified": False},
        "notes": ["Generated from a donor identity; populate only from verified evidence."]
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", required=True); parser.add_argument("--scene-guid", required=True); parser.add_argument("--name", default="World Generation Research Plan"); parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(); args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(build(args.build, args.scene_guid, args.name), indent=2) + "\n", encoding="utf-8"); print(args.output); return 0

if __name__ == "__main__": raise SystemExit(main())
