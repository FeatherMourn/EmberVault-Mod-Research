"""Derive gameplay-tuning candidates from the build-scoped KFC inventory."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(r"I:\My Drive\Enshrouded Mods\Control_Center")
INV = ROOT / "research" / "KFC_Tuning_Field_Inventory_1076226.json"
OUT = ROOT / "research" / "kfc_tuning_candidates_2026-09-25.json"

FAMILIES = {
    "GameSettings", "GameSettingsPresetsResource", "BalancingTable", "ItemInfo",
    "RecipeRegistryResource", "SkillTreeResource", "Perk", "BuffType",
    "BaseAttributeResource", "AttributeContainerResource", "LootableItemsResource",
    "TerraformingEfficiencyRegistryResource", "VoxelBlueprintConfig",
    "VoxelBlueprintItemRegistryResource", "VoxelBlueprintMaterialPoolRegistryResource",
    "BuildingMaterialParametersResource", "BuildingMaterialBlendingResource", "GliderConfig",
    "CameraStatesOverrideConfig", "CameraStatesManager", "IngameTimeConfig",
    "WeatherSystemResource", "RenderWeatherResource", "VolumetricFog3Resource",
    "VoxelWorldFog3Resource", "WaterWorldResource", "VoxelTemperatureResource",
    "DefaultInventoryResource", "GameKnowledgeResource", "ItemKnowledgeResource",
    "JournalRegistryResource", "EnemyArsenalRegistryResource", "TrashLootTableResource",
    "WorkshopRegistryResource", "AmbientParameterResource", "AmbientPostProcessingResource",
    "SamplerInstrumentResource",
}
KEYWORDS = ("health", "mana", "stamina", "damage", "health", "xp", "experience", "level", "skill", "perk", "cost", "yield", "stack", "loot", "rarity", "drop", "growth", "production", "durability", "fog", "shroud", "weather", "rain", "night", "day", "time", "glider", "camera", "radius", "terraform", "terrain", "building", "material", "buff", "duration", "crit", "altar", "recipe", "ingredient", "output", "comfort", "temperature", "water", "fishing", "knowledge", "inventory", "range", "speed", "resistance", "updraft", "yaw", "pitch", "roll", "acceleration")

def main() -> None:
    data = json.loads(INV.read_text(encoding="utf-8"))
    rows = []
    for family in data["families"]:
        if family["family"] not in FAMILIES:
            continue
        for reflected in family["reflected_types"]:
            for field in reflected["fields"]:
                name = field["name"]
                low = name.lower()
                if not any(k in low for k in KEYWORDS):
                    continue
                rows.append({
                    "id": f"{family['family']}.{name}",
                    "label": name,
                    "category": family["category"],
                    "target_resource": reflected["name"],
                    "target_field": name,
                    "type_index": field["type_index"],
                    "offset": field["offset"],
                    "status": "KFC_FIELD_CANDIDATE",
                    "application_mode": "EML_STARTUP_PATCH_REQUIRES_BEHAVIORAL_READBACK",
                    "restart_required": True,
                    "notes": "Reflected field; writable shape, authority, consumer, persistence, and safe revert remain to be verified.",
                })
    rows.sort(key=lambda r: (r["category"], r["id"]))
    OUT.write_text(json.dumps({"schema": "control_center.kfc_tuning_candidates.v1", "build": data["build"], "count": len(rows), "candidates": rows}, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}; candidates={len(rows)}")

if __name__ == "__main__":
    main()
