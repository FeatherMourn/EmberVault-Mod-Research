"""Build a read-only resource identity probe for undecodable KFC families."""
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
    parser.add_argument("resource_type")
    parser.add_argument("resource_guid")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "src").mkdir()
    project_id = args.output.name
    LuaAssistant().generate_resource_metadata_probe(
        args.resource_type, args.resource_guid, project_id, args.output / "src" / "mod.lua"
    )
    manifest = {
        "id": project_id, "name": "Control Center Resource Metadata Probe",
        "version": "0.1.0", "author": "Enshrouded Control Center",
        "capabilities": ["patch"], "feature_state": "research-only",
        "entrypoint": "src/mod.lua", "mode": "read_only_metadata_identity",
        "resource_type": args.resource_type, "resource_guid": args.resource_guid,
        "runtime_mutation": False,
    }
    (args.output / "mod.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Generated resource metadata probe: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
