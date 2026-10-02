"""Build a build-scoped KFC/reflection tuning inventory for Control Center."""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(r"I:\My Drive\Enshrouded Mods")
KFC = ROOT / "ENSHROUDED KFC FILES"
REFLECTION = Path(r"H:\enshroudedresearch\tools\kfc unpacked\reflection_data.json")
OUT = ROOT / "Control_Center" / "research" / "KFC_Tuning_Field_Inventory_1076226.json"
REPORT = ROOT / "Control_Center" / "research" / "KFC_Tuning_Field_Inventory_1076226.md"

KNOWN = {
    "GameSettings": "Game rules and difficulty",
    "GameSettingsPresetsResource": "Game rules and difficulty",
    "BalancingTable": "Balance and progression",
    "ItemInfo": "Items and equipment",
    "ItemRegistryResource": "Items and equipment",
    "RecipeRegistryResource": "Crafting and recipes",
    "SkillTreeResource": "Skills and progression",
    "Perk": "Skills and progression",
    "BuffType": "Buffs and attributes",
    "BaseAttributeResource": "Buffs and attributes",
    "AttributeContainerResource": "Buffs and attributes",
    "LootableItemsResource": "Loot and rewards",
    "TerraformingEfficiencyRegistryResource": "Terrain and mining",
    "VoxelBlueprintConfig": "Building and blueprints",
    "VoxelBlueprintItemRegistryResource": "Building and blueprints",
    "VoxelBlueprintMaterialPoolRegistryResource": "Building and blueprints",
    "BuildingMaterialParametersResource": "Building and materials",
    "BuildingMaterialBlendingResource": "Building and materials",
    "GliderConfig": "Movement and gliders",
    "CameraStatesOverrideConfig": "Camera",
    "CameraStatesManager": "Camera",
    "IngameTimeConfig": "Time",
    "WeatherSystemResource": "Weather and environment",
    "RenderWeatherResource": "Weather and environment",
    "VolumetricFog3Resource": "Fog and atmosphere",
    "VoxelWorldFog3Resource": "Fog and atmosphere",
    "WaterWorldResource": "Water and environment",
    "VoxelTemperatureResource": "Temperature and environment",
    "DefaultInventoryResource": "Inventory and starter loadout",
    "GameKnowledgeResource": "Knowledge and map",
    "ItemKnowledgeResource": "Knowledge and map",
    "JournalRegistryResource": "Knowledge and map",
    "EnemyArsenalRegistryResource": "Enemies and combat",
    "DevEnemyArsenalRegistryResource": "Enemies and combat",
    "TrashLootTableResource": "Loot and fishing",
    "WorkshopRegistryResource": "Workshops and production",
}

def base(name: str) -> str:
    name = name.split("::")[-1]
    name = re.sub(r"^(ObjectReference|BlobArray|DsArray)<.*>$", "", name)
    return name

def main() -> None:
    reflection = json.loads(REFLECTION.read_text(encoding="utf-8"))
    types = reflection["types"]
    by_name = {}
    for t in types:
        by_name.setdefault(base(t.get("name", "")), []).append(t)

    families = sorted(p.stem for p in KFC.glob("*.zip"))
    rows = []
    for family in families:
        matches = []
        for t in by_name.get(family, []):
            fields = []
            for f in (t.get("structFields") or {}).values():
                fields.append({"name": f["name"], "type_index": f.get("type"), "offset": f.get("dataOffset"), "attributes": f.get("attributes", {})})
            matches.append({"name": t.get("qualifiedName"), "index": t.get("index"), "size": t.get("size"), "primitive": t.get("primitiveType"), "fields": fields, "enums": list((t.get("enumFields") or {}).keys()), "attributes": t.get("attributes", {})})
        rows.append({"family": family, "category": KNOWN.get(family, "Other KFC family"), "archive": str(KFC / f"{family}.zip"), "reflected_type_count": len(matches), "reflected_types": matches})

    data = {"schema": "control_center.kfc_tuning_inventory.v1", "build": "1076226", "reflection_version": reflection.get("version"), "family_count": len(rows), "families": rows}
    OUT.write_text(json.dumps(data, indent=2), encoding="utf-8")

    mapped = sum(1 for r in rows if r["reflected_type_count"] and any(t["fields"] for t in r["reflected_types"]))
    lines = ["# KFC tuning field inventory — build 1076226", "", f"KFC families: {len(rows)}", f"Families with matching reflected concrete types: {mapped}", "", "This is a discovery inventory, not a claim that every field is writable or authoritative through EML.", "", "## Families with reflected fields", ""]
    for r in rows:
        field_names = []
        for t in r["reflected_types"]:
            field_names.extend(f["name"] for f in t["fields"])
        if not field_names:
            continue
        unique = list(dict.fromkeys(field_names))
        lines.append(f"### {r['family']} — {r['category']}")
        lines.append(f"Reflected types: {r['reflected_type_count']}; fields: {len(unique)}")
        lines.append("`" + "`, `".join(unique) + "`")
        lines.append("")
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"Wrote {REPORT}")
    print(f"Families={len(rows)}; reflected_with_fields={mapped}")

if __name__ == "__main__":
    main()
