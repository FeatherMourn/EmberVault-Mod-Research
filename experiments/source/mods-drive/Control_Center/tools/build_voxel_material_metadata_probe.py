"""Generate a bounded metadata-only classifier for one VoxelWorld GUID table."""
from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path


GUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)


def load_guids(archive_path: Path, donor_guid: str, part: int, max_guids: int) -> list[str]:
    donor_guid = donor_guid.lower()
    if not GUID_RE.fullmatch(donor_guid):
        raise ValueError("donor GUID is invalid")
    with zipfile.ZipFile(archive_path) as archive:
        candidates = []
        for item in archive.infolist():
            if donor_guid not in item.filename.lower() or not item.filename.lower().endswith(".json"):
                continue
            data = json.loads(archive.read(item).decode("utf-8-sig"))
            if int(data.get("$part", 0)) == part:
                candidates.append(data)
        if len(candidates) != 1:
            raise ValueError(f"expected exactly one donor part, found {len(candidates)}")
    values: list[str] = []
    for value in candidates[0].get("materialGuids", []):
        if value is None:
            continue
        guid = str(value).lower()
        if not GUID_RE.fullmatch(guid):
            raise ValueError(f"invalid table GUID: {guid}")
        if guid not in values:
            values.append(guid)
    if not values:
        raise ValueError("donor has no non-null material-table GUIDs")
    if len(values) > max_guids:
        raise ValueError(f"donor has {len(values)} GUIDs, above limit {max_guids}")
    return values


def build(archive_path: Path, donor_guid: str, part: int, output: Path, max_guids: int = 256) -> dict:
    guids = load_guids(archive_path, donor_guid, part, max_guids)
    probe_id = f"voxel_material_full_metadata_{donor_guid[:8]}_1076226"
    output.mkdir(parents=True, exist_ok=False)
    (output / "src").mkdir()
    manifest = {
        "id": probe_id,
        "name": "Control Center Full Voxel Material Metadata Probe",
        "version": "0.1.0",
        "author": "Enshrouded Control Center",
        "loader": "EML",
        "feature_state": "research-only",
        "capabilities": ["patch"],
        "entrypoint": "src/mod.lua",
        "compatible_game_builds": ["1076226"],
        "required_loader_api_version": "1.3",
        "research_build": "1076226",
        "mode": "metadata-only-read-only",
        "research_only": True,
        "source_world_guid": donor_guid.lower(),
        "source_world_part": part,
        "sample_count": len(guids),
    }
    (output / "mod.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    rows = "\n".join(f"  '{guid}'," for guid in guids)
    lua = f"""-- Generated metadata-only classifier; no payload or world access.
local PREFIX = '[CC-VOXEL-MATERIAL-FULL:{probe_id}] '
local GUIDS = {{
{rows}
}}
local function log(kind, value) print(PREFIX .. kind .. '|' .. tostring(value or '')) end
log('BEGIN', 'build=1076226|api=' .. tostring(game.api_version) .. '|read_only=true|metadata_only=true|sample=' .. tostring(#GUIDS))
if tostring(game.api_version) ~= '1.3' or type(game.assets.get_resource_metadata_by_guid) ~= 'function' then
  log('RESULT', 'api_mismatch') return {{}}
end
local resolved, matches = 0, 0
local types = {{}}
for _, guid in ipairs(GUIDS) do
  local ok, rows = pcall(function() return game.assets.get_resource_metadata_by_guid(guid) or {{}} end)
  local count = ok and #rows or 0
  if count > 0 then resolved = resolved + 1 end
  matches = matches + count
  log('GUID', guid .. '|ok=' .. tostring(ok) .. '|count=' .. tostring(count))
  if ok then
    for _, row in ipairs(rows) do
      local type_name = tostring(row.type)
      types[type_name] = (types[type_name] or 0) + 1
      log('MATCH', guid .. '|type=' .. type_name .. '|part=' .. tostring(row.part))
    end
  end
end
for type_name, count in pairs(types) do log('TYPE_COUNT', type_name .. '|count=' .. tostring(count)) end
log('BOUNDARY', 'payload=false|created=false|registered=false|mutated=false|world=false|save=false')
log('RESULT', 'voxel_material_full_metadata_complete|sample=' .. tostring(#GUIDS) .. '|resolved=' .. tostring(resolved) .. '|matches=' .. tostring(matches))
log('END', 'build=1076226')
return {{}}
"""
    (output / "src" / "mod.lua").write_text(lua, encoding="utf-8")
    return {"probe_id": probe_id, "guid_count": len(guids), "output": str(output.resolve())}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("donor_guid")
    parser.add_argument("output", type=Path)
    parser.add_argument("--part", type=int, default=0)
    parser.add_argument("--max-guids", type=int, default=256)
    args = parser.parse_args()
    print(json.dumps(build(args.archive, args.donor_guid, args.part, args.output, args.max_guids), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
