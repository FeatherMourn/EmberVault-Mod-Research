"""Build a bounded, read-only Construction Hammer registry payload probe."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.lua_assistant import LuaAssistant


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("resource_guid")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "src").mkdir()
    LuaAssistant().generate_blueprint_registry_payload_probe(
        args.resource_guid,
        project_id=args.output.name,
        destination=args.output / "src" / "mod.lua",
    )
    manifest = {
        "schema": "control_center.blueprint_registry_payload_probe.v1",
        "id": args.output.name,
        "name": "Control Center Bounded Blueprint Registry Payload Probe",
        "version": "0.1.0",
        "feature_state": "research-only",
        "mode": "read_only_bounded_payload",
        "capabilities": ["patch"],
        "entrypoint": "src/mod.lua",
        "research_build": "1076226",
        "resource_type": "keen::VoxelBlueprintItemRegistryResource",
        "resource_guid": args.resource_guid,
        "mutation": {"allowed": False, "requires_separate_probe": True},
    }
    (args.output / "mod.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Generated bounded blueprint payload probe: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
