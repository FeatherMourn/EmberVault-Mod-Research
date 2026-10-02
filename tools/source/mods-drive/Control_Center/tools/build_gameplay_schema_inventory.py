"""Build a conservative inventory of reflected gameplay-schema candidates.

This is discovery evidence only. Presence in reflection/KFC data does not
prove that a resource is loaded, writable, persistent, or authoritative.
"""
from __future__ import annotations

import json
import re
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KFC_ROOT = ROOT.parent / "ENSHROUDED KFC FILES"
REFLECTION = Path(r"H:\enshroudedresearch\tools\kfc unpacked\reflection_data.json")
JSON_OUT = ROOT / "research" / "GAMEPLAY_SCHEMA_INVENTORY_1076226.json"
MD_OUT = ROOT / "research" / "GAMEPLAY_SCHEMA_INVENTORY_1076226.md"

FAMILIES = {
    "interaction": ("Interaction", "Action", "Use", "Pickup", "Placement", "Storage"),
    "ai": ("Enemy", "Behavior", "Arsenal", "Combat", "Spawn"),
    "quest": ("Quest", "Objective", "Dialogue", "Journal", "Progression", "WorldEvent"),
    "animation": ("Animation", "Anim", "StateMachine", "VfxEvent"),
    "world_generation": ("World", "Generation", "Terrain", "Voxel", "Biome"),
    "multiplayer_authority": ("Network", "Replication", "Authority", "Server", "Permission"),
}


def base_name(value: str) -> str:
    value = value.split("::")[-1]
    return re.sub(r"^(ObjectReference|BlobArray|DsArray)<.*>$", "", value)


def category(name: str) -> str | None:
    lowered = base_name(name).lower()
    for group, needles in FAMILIES.items():
        if any(needle.lower() in lowered for needle in needles):
            return group
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reflection", type=Path, default=REFLECTION,
                        help="reflection/types JSON for the target build")
    parser.add_argument("--kfc-root", type=Path, default=KFC_ROOT,
                        help="directory containing extracted KFC archives")
    parser.add_argument("--output-dir", type=Path, default=JSON_OUT.parent,
                        help="directory for the JSON and Markdown reports")
    args = parser.parse_args()
    reflection = json.loads(args.reflection.read_text(encoding="utf-8"))
    json_out = args.output_dir / JSON_OUT.name
    md_out = args.output_dir / MD_OUT.name
    reflected: dict[str, list[dict[str, object]]] = {key: [] for key in FAMILIES}
    for item in reflection.get("types", []):
        group = category(str(item.get("qualifiedName", item.get("name", ""))))
        if group is None or item.get("primitiveType") != "STRUCT":
            continue
        fields = []
        for field in (item.get("structFields") or {}).values():
            fields.append({
                "name": field.get("name"),
                "type_index": field.get("type"),
                "offset": field.get("dataOffset"),
            })
        reflected[group].append({
            "name": item.get("qualifiedName"),
            "index": item.get("index"),
            "size": item.get("size"),
            "field_count": item.get("fieldCount", 0),
            "fields": fields,
        })

    archives = {path.stem for path in args.kfc_root.glob("*.zip")}
    groups = []
    for group, candidates in reflected.items():
        names = sorted({base_name(str(row["name"])) for row in candidates})
        groups.append({
            "area": group,
            "candidate_count": len(candidates),
            "candidate_types": sorted(candidates, key=lambda row: str(row["name"])),
            "matching_kfc_archives": sorted(name for name in archives if category(name) == group),
            "runtime_mutation": False,
            "authority": "unknown",
            "status": "research-only",
            "next_step": "select one donor and run a bounded read-only metadata probe",
            "candidate_names": names,
        })
    result = {
        "schema": "control_center.gameplay_schema_inventory.v1",
        "build": reflection.get("version", "1076226"),
        "source": str(REFLECTION),
        "groups": groups,
        "safety": "Discovery evidence only; no resource writes or runtime claims are made.",
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Gameplay schema inventory — build 1076226",
        "",
        "This inventory is reflection/KFC discovery evidence only. It does not prove that a family is loaded, writable, persistent, or multiplayer-authoritative.",
        "",
    ]
    for group in groups:
        lines.extend([
            f"## {group['area']}",
            "",
            f"Reflected struct candidates: {group['candidate_count']}",
            f"Matching KFC archives: {len(group['matching_kfc_archives'])}",
            "",
        ])
        for row in group["candidate_types"][:40]:
            fields = ", ".join(str(field["name"]) for field in row["fields"][:20])
            lines.append(f"- `{row['name']}` — {row['field_count']} fields" + (f": {fields}" if fields else ""))
        if group["candidate_count"] > 40:
            lines.append(f"- … {group['candidate_count'] - 40} additional reflected candidates omitted from the compact report")
        lines.extend(["", f"Next step: {group['next_step']}.", ""])
    md_out.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"schema": result["schema"], "groups": {group["area"]: group["candidate_count"] for group in groups}, "json": str(json_out), "markdown": str(md_out)}, indent=2))


if __name__ == "__main__":
    main()
