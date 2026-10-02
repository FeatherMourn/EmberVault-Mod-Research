"""Build a fail-closed research probe for one bounded animation graph variant."""
from __future__ import annotations

import argparse
import json
import re
import uuid
from pathlib import Path

SCHEMA = "control_center.animation_graph_variant.v1"
GRAPH_TYPE = "keen::anim_graph::runtime_graph::AnimationGraphResource2_0"
OWNER_TYPE = "keen::NpcCollection"
OWNER_FIELD = "uiRendering.animationGraph2"
REQUIRED_PROHIBITIONS = {
    "modify-donor", "modify-template", "create-or-mutate-entity",
    "write-world", "write-save", "modify-animation-payload",
}

def lua_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)

def validate(data: dict) -> list[str]:
    errors: list[str] = []
    if data.get("schema") != SCHEMA: errors.append("unsupported definition schema")
    if data.get("feature_state") != "research-only": errors.append("feature_state must be research-only")
    if data.get("graph_type") != GRAPH_TYPE: errors.append("unsupported graph type")
    for field in ("donor_guid", "clone_guid"):
        try: uuid.UUID(str(data.get(field, "")))
        except ValueError: errors.append(f"{field} must be a UUID")
    if data.get("donor_guid") == data.get("clone_guid"): errors.append("clone_guid must differ from donor_guid")
    if not re.fullmatch(r"[a-z][a-z0-9_]{2,63}", str(data.get("id", ""))): errors.append("id must be a safe module identifier")
    owner = data.get("owner") if isinstance(data.get("owner"), dict) else {}
    if owner.get("type") != OWNER_TYPE: errors.append("owner type must be keen::NpcCollection")
    if owner.get("field") != OWNER_FIELD: errors.append("owner field must be uiRendering.animationGraph2")
    try: uuid.UUID(str(owner.get("guid", "")))
    except ValueError: errors.append("owner guid must be a UUID")
    if not str(owner.get("entry_debug_name", "")).strip(): errors.append("owner entry_debug_name is required")
    edit = data.get("edit") if isinstance(data.get("edit"), dict) else {}
    if edit.get("kind") != "state_pose_redirect": errors.append("only state_pose_redirect is supported")
    if edit.get("same_graph_existing_pose") is not True: errors.append("replacement must be an existing pose in the same graph")
    for field in ("state_id", "expected_pose_id", "replacement_pose_id"):
        if not isinstance(edit.get(field), int) or edit[field] <= 0: errors.append(f"edit {field} must be a positive integer")
    if edit.get("expected_pose_id") == edit.get("replacement_pose_id"): errors.append("replacement pose must differ from expected pose")
    if not str(edit.get("state_name", "")).strip() or not str(edit.get("replacement_state_name", "")).strip(): errors.append("state names are required")
    prohibitions = set(data.get("prohibited_actions", []))
    missing = sorted(REQUIRED_PROHIBITIONS - prohibitions)
    if missing: errors.append("missing prohibited actions: " + ", ".join(missing))
    return errors

def render(data: dict) -> str:
    owner, edit = data["owner"], data["edit"]
    constants = {
        "MODULE_ID": data["id"], "GRAPH_TYPE": data["graph_type"],
        "DONOR_GUID": data["donor_guid"], "CLONE_GUID": data["clone_guid"],
        "OWNER_TYPE": owner["type"], "OWNER_GUID": owner["guid"], "OWNER_NAME": owner["entry_debug_name"],
        "STATE_NAME": edit["state_name"], "TARGET_STATE_NAME": edit["replacement_state_name"],
    }
    lines = ["-- Generated bounded animation graph variant; research-only."]
    for name, value in constants.items(): lines.append(f"local {name} = {lua_string(value)}")
    lines.extend([
        f"local STATE_ID = {edit['state_id']}", f"local EXPECTED_POSE = {edit['expected_pose_id']}",
        f"local REPLACEMENT_POSE = {edit['replacement_pose_id']}",
        "local PREFIX = '[CC-ANIMATION-VARIANT:' .. MODULE_ID .. '] '",
        "local function log(kind,value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end",
        "local function safe(fn) local ok,value=pcall(fn); if ok then return value end; return nil end",
        "log('BEGIN','build=" + str(data["game_build"]) + "|api=' .. tostring(game.api_version) .. '|research_only=true')",
        "local donor=safe(function() return game.assets.get_resource(DONOR_GUID,GRAPH_TYPE,0) end)",
        "if not donor or not donor.data then log('RESULT','donor_lookup_failed'); return {} end",
        "if safe(function() return game.assets.get_resource(CLONE_GUID,GRAPH_TYPE,0) end) then log('RESULT','clone_guid_collision'); return {} end",
        "local ok,clone=pcall(function() return game.assets.register_resource(donor.data,GRAPH_TYPE,CLONE_GUID,0) end)",
        "if not ok or not clone or not clone.data then log('RESULT','clone_registration_failed|' .. tostring(clone)); return {} end",
        "local edited,before,after=0,nil,nil",
        "for _,node in pairs(clone.data.nodeDefinitions or {}) do local value=safe(function() return node.value end); if value and tonumber(safe(function() return value.id.value end))==STATE_ID then before=tonumber(safe(function() return value.poseResult.value end)); if before~=EXPECTED_POSE then log('RESULT','state_pose_mismatch|before=' .. tostring(before)); return {} end; value.poseResult.value=REPLACEMENT_POSE; after=tonumber(value.poseResult.value); edited=edited+1 end end",
        "if edited~=1 or after~=REPLACEMENT_POSE then log('RESULT','edit_cardinality_failed|edited=' .. edited); return {} end",
        "log('GRAPH_EDIT','state=' .. STATE_NAME .. '|stateId=' .. STATE_ID .. '|beforePose=' .. before .. '|afterPose=' .. after .. '|targetState=' .. TARGET_STATE_NAME)",
        "local owner=safe(function() return game.assets.get_resource(OWNER_GUID,OWNER_TYPE,0) end)",
        "if not owner or not owner.data then log('RESULT','owner_lookup_failed'); return {} end",
        "local target,matches=nil,0; for _,entry in pairs(owner.data.npcs or {}) do if tostring(entry.debugName)==OWNER_NAME then target=entry;matches=matches+1 end end",
        "if not target or matches~=1 then log('RESULT','owner_cardinality_failed|matches=' .. matches); return {} end",
        "local owner_before=tostring(target.uiRendering and target.uiRendering.animationGraph2 or '')",
        "if owner_before~=DONOR_GUID then log('RESULT','owner_reference_mismatch|before=' .. owner_before); return {} end",
        "target.uiRendering.animationGraph2=CLONE_GUID",
        "log('ATTACHMENT','owner=' .. OWNER_NAME .. '|field=uiRendering.animationGraph2|before=' .. owner_before .. '|after=' .. tostring(target.uiRendering.animationGraph2))",
        "log('BOUNDARY','donor=false|template=false|entity=false|world=false|save=false|animationPayload=false')",
        "log('RESULT','animation_graph_variant_attached')", "return {}", "",
    ])
    return "\n".join(lines)

def build(definition: Path, output: Path) -> dict:
    data = json.loads(Path(definition).read_text(encoding="utf-8-sig"))
    errors = validate(data)
    if errors: raise ValueError("; ".join(errors))
    if output.exists(): raise FileExistsError(f"output already exists: {output}")
    (output / "src").mkdir(parents=True)
    (output / "src" / "mod.lua").write_text(render(data), encoding="utf-8")
    manifest = {
        "schema": "control_center.animation_graph_variant_probe.v1", "id": data["id"],
        "name": f"Control Center Animation Variant: {data['id']}", "version": "0.1.0",
        "author": "Enshrouded Control Center", "feature_state": "research-only", "capabilities": ["patch"],
        "entrypoint": "src/mod.lua", "compatible_game_builds": [str(data["game_build"])],
        "required_loader_api_version": str(data["required_loader_api_version"]),
        "runtime_mutation": True, "attach_behavior": True, "rollback_required": True,
        "definition": data,
    }
    (output / "mod.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("definition",type=Path);parser.add_argument("output",type=Path);args=parser.parse_args()
    try: build(args.definition,args.output)
    except (OSError,ValueError,json.JSONDecodeError) as exc: parser.error(str(exc))
    print(f"Generated animation graph variant probe: {args.output}");return 0

if __name__ == "__main__": raise SystemExit(main())
