"""Generate a clone-only ItemInfo visual-reference assignment probe."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from core.lua_assistant import LuaAssistant

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("donor_guid")
    p.add_argument("new_item_id", type=int)
    p.add_argument("replacement_model_guid")
    p.add_argument("output", type=Path)
    args = p.parse_args()
    if args.new_item_id <= 0: p.error("new_item_id must be positive")
    args.output.mkdir(parents=True, exist_ok=False)
    source = LuaAssistant().generate_item_visual_reference_probe(
        args.donor_guid, args.new_item_id, args.replacement_model_guid,
        args.output.name, args.output / "src" / "mod.lua")
    manifest = {
        "id": args.output.name, "name": "Control Center Clone-Only Visual Reference Probe",
        "version": "0.1.0", "author": "Enshrouded Control Center",
        "capabilities": ["patch"], "feature_state": "research-only", "entrypoint": "src/mod.lua",
        "feature_state": "research-only", "mode": "clone_only_visual_assignment",
        "donor_guid": args.donor_guid, "new_item_id": args.new_item_id,
        "replacement_model_guid": args.replacement_model_guid,
        "runtime_mutation": False,
    }
    (args.output / "mod.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Generated clone-only visual assignment probe: {args.output}")
    return 0

if __name__ == "__main__": raise SystemExit(main())
