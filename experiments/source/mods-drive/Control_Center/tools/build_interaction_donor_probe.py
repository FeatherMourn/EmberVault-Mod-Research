"""Build a read-only, asset-backed interaction donor inspection probe."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.lua_assistant import LuaAssistant

parser = argparse.ArgumentParser()
parser.add_argument("--resource-type", required=True)
parser.add_argument("--donor-guid", required=True)
parser.add_argument("--interaction-key", default="")
parser.add_argument("--name", required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
resource_type = args.resource_type.strip()
donor_guid = args.donor_guid.strip()
if "TemplateResource" in resource_type:
    raise SystemExit("refusing interaction probe for quarantined TemplateResource family")
if donor_guid.lower() in {"donor-guid", "placeholder", "example"}:
    raise SystemExit("donor GUID must be a real build-specific resource GUID")
try:
    UUID(donor_guid)
except ValueError as exc:
    raise SystemExit("donor GUID must be a valid UUID") from exc
args.output.mkdir(parents=True, exist_ok=True); (args.output / "src").mkdir(parents=True, exist_ok=True)
mod_id = "control_center_interaction_donor_" + args.name.lower().replace("-", "_").replace(" ", "_")
LuaAssistant().generate_interaction_donor_probe(resource_type, donor_guid, args.interaction_key, mod_id, args.output / "src" / "mod.lua")
(args.output / "mod.json").write_text(json.dumps({
    "schema": "control_center.interaction_donor_probe.v1",
    "id": mod_id, "name": "Control Center Interaction Donor - " + args.name,
    "version": "0.1.0", "author": "Enshrouded Control Center",
    "capabilities": ["patch"], "feature_state": "research-only",
    "entrypoint": "src/mod.lua", "mode": "read_only_asset_backed_interaction_inspection",
    "resource_type": resource_type, "donor_guid": donor_guid,
    "interaction_key": args.interaction_key, "runtime_mutation": False,
    "execution_scope": "single-player-read-only",
}, indent=2) + "\n", encoding="utf-8")
print(f"Generated {mod_id} at {args.output}")
