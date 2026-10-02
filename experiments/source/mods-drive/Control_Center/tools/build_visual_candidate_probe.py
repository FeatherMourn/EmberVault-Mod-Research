"""Generate a read-only isolated probe for a visual candidate graph."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.lua_assistant import LuaAssistant


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--resource-type", default="keen::RenderModel")
    parser.add_argument("--build", default="unknown")
    args = parser.parse_args()
    try:
        raw_candidate = args.candidate.read_bytes()
        data = json.loads(raw_candidate.decode("utf-8-sig"))
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    # The probe checks the candidate GUID plus direct material GUIDs. Nested
    # packed texture references remain a separate research boundary.
    candidate_guid = str(data.get("$guid", "")).strip() or args.candidate.stem.split("_")[0]
    try:
        candidate_guid = str(uuid.UUID(candidate_guid))
    except ValueError:
        parser.error("candidate filename must begin with a valid resource GUID")
    dependencies = [candidate_guid]
    for item in data.get("materials", []):
        if isinstance(item, dict) and isinstance(item.get("material"), str):
            dependencies.append(item["material"])
    dependencies = list(dict.fromkeys(dependencies))
    args.output.mkdir(parents=True, exist_ok=True)
    source = LuaAssistant().generate_visual_substitution_probe(
        args.resource_type, dependencies, args.output.name, args.output / "src" / "mod.lua"
    )
    manifest = {
        "id": args.output.name,
        "name": f"Control Center Visual Candidate Probe ({candidate_guid[:8]})",
        "version": "0.1.0",
        "author": "Enshrouded Control Center",
        "capabilities": ["patch"],
        "entrypoint": "src/mod.lua",
        "feature_state": "research-only",
        "mode": "read_only_visual_candidate_probe",
        "research_build": args.build,
        "candidate": str(args.candidate),
        "candidate_sha256": hashlib.sha256(raw_candidate).hexdigest(),
        "resource_type": args.resource_type,
        "dependency_guids": dependencies,
        "runtime_mutation": False,
    }
    (args.output / "mod.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (args.output / "probe_manifest.json").write_text(json.dumps({
        "schema": "control_center.visual_candidate_probe_manifest.v1",
        "candidate": str(args.candidate),
        "candidate_sha256": hashlib.sha256(raw_candidate).hexdigest(),
        "dependencies": dependencies,
        "runtime_mutation": False,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Generated read-only visual candidate probe: {args.output}")
    print(f"Dependency count: {len(dependencies)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
