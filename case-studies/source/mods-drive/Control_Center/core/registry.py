"""Registry-driven tuning metadata, search and safe profile migration."""
from __future__ import annotations
import json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any

TUNING_CATEGORIES = ("Player & Survival", "Movement & Traversal", "Camera & View", "Combat & Enemies", "Building & Terrain", "Crafting & Inventory", "World & Environment", "Progression & Rewards", "Audio & Music", "Advanced Research")
SUBCATEGORIES = {
    "Player & Survival": ("Vitals & Attributes", "Survival", "Buffs & Status Effects", "Character Appearance"),
    "Movement & Traversal": ("General Movement", "Gliders", "Grappling"), "Camera & View": ("Free Camera", "Field of View", "Camera States"),
    "Combat & Enemies": ("Player Damage", "Enemies & Bosses", "Combat Perks"), "Building & Terrain": ("Construction", "Mining & Terraforming", "Building Materials", "Blueprints"),
    "Crafting & Inventory": ("Recipes", "Production", "Inventory", "Equipment"), "World & Environment": ("Day & Night", "Lighting & Weather", "Fog & Atmosphere", "Farming"),
    "Progression & Rewards": ("Experience", "Levels & Skills", "Knowledge & Discovery", "Loot & Fishing"), "Audio & Music": ("Instruments", "Music Buffs"),
}
MODULE_CATEGORY = {"survival_qol":"Player & Survival", "architect_companion":"Building & Terrain", "progression_balancing":"Progression & Rewards", "world_and_difficulty":"World & Environment", "inventory_and_items":"Crafting & Inventory", "crafting_and_recipes":"Crafting & Inventory", "skills_and_perks":"Progression & Rewards", "building_and_architecture":"Building & Terrain", "starter_loadout":"Player & Survival", "buffs_and_status":"Player & Survival", "environment_time_weather":"World & Environment", "loot_and_chests":"Progression & Rewards", "terraforming_and_mining":"Building & Terrain", "music_and_instruments":"Audio & Music", "knowledge_and_map":"Progression & Rewards", "actor_scaling_proportions":"Player & Survival", "custom_gliders_and_hooks":"Movement & Traversal"}

# Field-level targets for the settings that have a concrete mapping in the
# current EML/KFC research.  These are deliberately explicit: a profile key
# is not treated as an engine control merely because its label sounds plausible.
FIELD_MAP: dict[tuple[str, str], tuple[str, str]] = {
    ("survival_qol", "stack_multiplier"): ("keen::ItemInfo", "maxStackSize"),
    ("survival_qol", "shroud_time_multiplier"): ("keen::BalancingTable", "playerBaseFogResistance"),
    ("survival_qol", "infinite_durability"): ("keen::GameSettingsPresetsResource", "minValues.enableDurability / maxValues.enableDurability"),
    ("survival_qol", "stamina_cost_reduction"): ("keen::GameSettingsPresetsResource", "minValues.playerStaminaFactor / maxValues.playerStaminaFactor"),
    ("progression_balancing", "player_level_cap"): ("keen::BalancingTable", "playerLevelCap"),
    ("progression_balancing", "item_level_cap"): ("keen::BalancingTable", "itemLevelCap"),
    ("progression_balancing", "shroud_fog_resistance_multiplier"): ("keen::BalancingTable", "playerBaseFogResistance"),
    ("progression_balancing", "player_base_health"): ("keen::BalancingTable", "playerBaseHealth"),
    ("progression_balancing", "player_base_stamina"): ("keen::BalancingTable", "playerBaseStamina"),
    ("progression_balancing", "player_base_mana"): ("keen::BalancingTable", "playerBaseMana"),
    ("progression_balancing", "skill_points_per_level"): ("keen::BalancingTable", "skillPointsPerLevel"),
    ("progression_balancing", "ap_per_flame_level"): ("keen::BalancingTable", "apPerFlameLevel"),
    ("progression_balancing", "base_crit_chance"): ("keen::BalancingTable", "baseCritChance"),
    ("progression_balancing", "crit_bonus_multiplier"): ("keen::BalancingTable", "critBonus"),
    ("progression_balancing", "altars_per_flame_level"): ("keen::BalancingTable", "altarsPerFlameLevel"),
    ("world_and_difficulty", "enemy_damage_factor"): ("keen::ecs::GameSettings", "enemyDamageFactor"),
    ("world_and_difficulty", "enemy_health_factor"): ("keen::ecs::GameSettings", "enemyHealthFactor"),
    ("world_and_difficulty", "boss_damage_factor"): ("keen::ecs::GameSettings", "bossDamageFactor"),
    ("world_and_difficulty", "boss_health_factor"): ("keen::ecs::GameSettings", "bossHealthFactor"),
    ("world_and_difficulty", "pacify_all_enemies"): ("keen::ecs::GameSettings", "pacifyAllEnemies"),
    ("world_and_difficulty", "experience_combat_factor"): ("keen::ecs::GameSettings", "experienceCombatFactor"),
    ("world_and_difficulty", "experience_mining_factor"): ("keen::ecs::GameSettings", "experienceMiningFactor"),
    ("world_and_difficulty", "resource_drop_stack_factor"): ("keen::ecs::GameSettings", "resourceDropStackAmountFactor"),
    ("world_and_difficulty", "mining_damage_factor"): ("keen::ecs::GameSettings", "miningDamageFactor"),
    ("world_and_difficulty", "plant_growth_speed_factor"): ("keen::ecs::GameSettings", "plantGrowthSpeedFactor"),
    ("world_and_difficulty", "factory_production_speed_factor"): ("keen::ecs::GameSettings", "factoryProductionSpeedFactor"),
    ("world_and_difficulty", "disable_durability"): ("keen::ecs::GameSettings", "enableDurability"),
    ("world_and_difficulty", "food_buff_duration_factor"): ("keen::ecs::GameSettings", "foodBuffDurationFactor"),
    ("world_and_difficulty", "player_health_factor"): ("keen::ecs::GameSettings", "playerHealthFactor"),
    ("world_and_difficulty", "player_mana_factor"): ("keen::ecs::GameSettings", "playerManaFactor"),
    ("world_and_difficulty", "player_stamina_factor"): ("keen::ecs::GameSettings", "playerStaminaFactor"),
    ("world_and_difficulty", "player_body_heat_factor"): ("keen::ecs::GameSettings", "playerBodyHeatFactor"),
    ("world_and_difficulty", "player_diving_time_factor"): ("keen::ecs::GameSettings", "playerDivingTimeFactor"),
    ("world_and_difficulty", "enable_starving_debuff"): ("keen::ecs::GameSettings", "enableStarvingDebuff"),
    ("world_and_difficulty", "shroud_time_factor"): ("keen::ecs::GameSettings", "shroudTimeFactor"),
    ("world_and_difficulty", "enable_glider_turbulences"): ("keen::ecs::GameSettings", "enableGliderTurbulences"),
    ("world_and_difficulty", "weather_frequency"): ("keen::ecs::GameSettings", "weatherFrequency"),
    ("world_and_difficulty", "fishing_difficulty"): ("keen::ecs::GameSettings", "fishingDifficulty"),
    ("world_and_difficulty", "enemy_stamina_factor"): ("keen::ecs::GameSettings", "enemyStaminaFactor"),
    ("world_and_difficulty", "enemy_perception_range_factor"): ("keen::ecs::GameSettings", "enemyPerceptionRangeFactor"),
    ("world_and_difficulty", "threat_bonus"): ("keen::ecs::GameSettings", "threatBonus"),
    ("world_and_difficulty", "random_spawner_amount"): ("keen::ecs::GameSettings", "randomSpawnerAmount"),
    ("world_and_difficulty", "aggro_pool_amount"): ("keen::ecs::GameSettings", "aggroPoolAmount"),
    ("world_and_difficulty", "day_time_duration"): ("keen::ecs::GameSettings", "dayTimeDuration"),
    ("world_and_difficulty", "night_time_duration"): ("keen::ecs::GameSettings", "nightTimeDuration"),
    ("world_and_difficulty", "taming_startle_repercussion"): ("keen::ecs::GameSettings", "tamingStartleRepercussion"),
    ("world_and_difficulty", "curse_modifier"): ("keen::ecs::GameSettings", "curseModifier"),
    ("building_and_architecture", "altar_build_radius_mult"): ("keen::BalancingTable", "buildzoneSizesPerAltarLevel"),
    ("terraforming_and_mining", "terraforming_speed_multiplier"): ("keen::TerraformingEfficiencyRegistryResource", "terrainConfigs / buildingConfigs"),
    ("inventory_and_items", "max_stack_multiplier"): ("keen::ItemInfo", "maxStackSize"),
    ("crafting_and_recipes", "ingredient_cost_discount_pct"): ("keen::RecipeRegistryResource", "recipe inputs"),
    ("crafting_and_recipes", "recipe_yield_multiplier"): ("keen::RecipeRegistryResource", "recipe outputs"),
    ("loot_and_chests", "legendary_drop_rate_boost"): ("keen::LootableItemsResource", "rarity / label groups"),
    ("loot_and_chests", "trash_fishing_probability_pct"): ("keen::fishing::TrashLootTableResource", "trash loot probability"),
    ("starter_loadout", "starting_potion_count"): ("keen::DefaultInventoryResource", "starter inventory entries"),
    ("starter_loadout", "starting_runes"): ("keen::DefaultInventoryResource", "starter inventory entries"),
    ("buffs_and_status", "buff_lifetime_multiplier"): ("keen::BuffType", "duration fields"),
    ("buffs_and_status", "persist_buffs_through_death"): ("keen::BuffType", "despawnOnDeath"),
    ("music_and_instruments", "instrument_comfort_buff_mult"): ("keen::BalancingTable", "instrument comfort values"),
    ("music_and_instruments", "instrument_volume_boost"): ("keen::SamplerInstrumentResource", "instrument volume"),
}

def _placement(module_id: str, key: str) -> tuple[str, str, tuple[str, ...]]:
    k = key.lower()
    if module_id == "architect_companion" and "camera" in k: return "Camera & View", "Field of View" if "fov" in k else "Free Camera", ("camera", "view")
    if module_id == "architect_companion" and "freecam" in k: return "Camera & View", "Free Camera", ("flight", "camera")
    if module_id == "architect_companion" and "altar" in k: return "Building & Terrain", "Construction", ("altar", "building")
    if "glider" in k: return "Movement & Traversal", "Gliders", ("movement", "traversal")
    if "grapple" in k: return "Movement & Traversal", "Grappling", ("movement", "hook")
    if module_id == "survival_qol": return "Player & Survival", "Survival", ("survival", "player")
    if module_id == "buffs_and_status": return "Player & Survival", "Buffs & Status Effects", ("buff", "status")
    if module_id == "actor_scaling_proportions":
        if any(token in k for token in ("enemy", "npc")): return "Combat & Enemies", "Enemies & Bosses", ("scaling", "enemy", "npc")
        return "Player & Survival", "Character Appearance", ("character", "appearance", "scaling")
    if module_id.startswith("custom_hair"): return "Player & Survival", "Character Appearance", ("character", "appearance")
    if module_id == "skills_and_perks": return "Progression & Rewards", "Levels & Skills", ("skills", "perks")
    if module_id == "knowledge_and_map": return "Progression & Rewards", "Knowledge & Discovery", ("map", "knowledge")
    if module_id == "loot_and_chests": return "Progression & Rewards", "Loot & Fishing", ("loot", "rewards")
    if module_id == "crafting_and_recipes": return "Crafting & Inventory", "Recipes" if "recipe" in k else "Production", ("crafting", "recipes")
    if module_id == "inventory_and_items": return "Crafting & Inventory", "Inventory", ("items", "equipment")
    if module_id == "terraforming_and_mining": return "Building & Terrain", "Mining & Terraforming", ("terrain", "mining")
    if module_id.startswith("custom_building"): return "Building & Terrain", "Building Materials", ("materials", "building")
    if module_id == "building_and_architecture": return "Building & Terrain", "Construction", ("building", "construction")
    if module_id == "environment_time_weather": return "World & Environment", "Lighting & Weather", ("weather", "world")
    if module_id == "custom_farming_and_botany": return "World & Environment", "Farming", ("farming", "crops")
    if module_id == "music_and_instruments" or module_id.startswith("custom_music"): return "Audio & Music", "Instruments" if "instrument" in k else "Music Buffs", ("audio", "music")
    if module_id == "progression_balancing": return "Progression & Rewards", "Levels & Skills", ("progression", "levels")
    if module_id == "world_and_difficulty": return ("Combat & Enemies", "Enemies & Bosses", ("combat", "world")) if ("enemy" in k or "boss" in k) else ("World & Environment", "Lighting & Weather", ("world",))
    if module_id == "custom_weapons_and_armor": return "Combat & Enemies", "Player Damage", ("weapons", "combat")
    return MODULE_CATEGORY.get(module_id, "Advanced Research"), "Survival", (module_id,)

def _type_and_units(setting: dict[str, Any]) -> tuple[str, str | None, int | None]:
    if setting.get("type") == "toggle": return "boolean", None, None
    label = str(setting.get("label", "")).lower()
    if "percent" in label or "reduction" in label or "discount" in label: return "percentage", "%", 1
    if "multiplier" in label or "factor" in label: return "multiplier", "×", 2
    return "number", None, 2 if isinstance(setting.get("default"), float) else 0

@dataclass(frozen=True)
class SettingDefinition:
    id: str; label: str; description: str; category: str; input_type: str; units: str | None; declared_min: float | int | None; declared_max: float | int | None; step: float | int | None; precision: int | None; vanilla_value: Any; profile_default: Any; target_resource: str | None; target_field: str | None; evidence: str; compatible_game_build: str | None; validation_state: str; application_mode: str; output_mapping: str; legacy_key: str
    subcategory: str = ""; tags: tuple[str, ...] = field(default_factory=tuple); restart_required: bool = True; vanilla_evidence: str = "Vanilla value unverified"; reset_eligible: bool = False
    def deployable(self) -> bool: return self.validation_state == "Available" and self.application_mode == "Generated Lua"

class SettingRegistry:
    def __init__(self, base_dir: Path, manager): self.base_dir, self.manager = Path(base_dir), manager
    def definitions(self) -> list[SettingDefinition]:
        result = []
        for module_id, module in sorted(self.manager.modules.items()):
            # The tuning map must reflect deployable policy, not merely every
            # manifest present on disk. Shipped custom/unverified modules are
            # hidden here; their candidates remain visible in Advanced
            # Research through research(). Unknown module IDs stay available
            # for isolated extensions and tests.
            if hasattr(self.manager, "_is_verified_module") and not self.manager._is_verified_module(module_id):
                continue
            resources = module.get("target_kfc_resources", [])
            for setting in module.get("settings", []):
                category, subcategory, tags = _placement(module_id, setting["key"]); typ, units, precision = _type_and_units(setting)
                # Keep reset eligibility independent from restart semantics.  A
                # profile default is never a vanilla value; reset eligibility
                # can only be granted by explicit, independently verified
                # metadata (or a separately verified override-removal route).
                # Control Center policy: every tuning change is restart-required.
                # Keep the manifest's dynamic flag for historical compatibility,
                # but never advertise a live control in the UI.
                restart_required = True
                resource_field = FIELD_MAP.get((module_id, setting["key"]))
                target_resource = resource_field[0] if resource_field else (resources[0] if resources else None)
                target_field = resource_field[1] if resource_field else None
                reset_eligible = bool(setting.get("vanilla_verified", False)) and setting.get("vanilla") is not None
                result.append(SettingDefinition(f"{module_id}.{setting['key']}", setting.get("label", setting["key"]), setting.get("tooltip", module.get("description", "")), category, typ, units, setting.get("min"), setting.get("max"), setting.get("step"), precision, setting.get("vanilla") if reset_eligible else None, setting.get("default"), target_resource, target_field, f"modules/{module_id}/module.json; modules/{module_id}/{module.get('entrypoint','patch.lua')}", (module.get("compatible_game_builds") or [None])[0], "Available", "Generated Lua", f"module_settings.{module_id}.{setting['key']}", f"module_settings.{module_id}.{setting['key']}", subcategory, tuple(sorted(set(tags + (module_id, setting["key"].lower())))), restart_required, "Verified vanilla value" if reset_eligible else "Vanilla value unverified", reset_eligible))
        return result
    def research(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        legacy = self.base_dir / "research" / "kfc_candidates_2026-09-24.json"
        if legacy.is_file():
            items.extend(json.loads(legacy.read_text(encoding="utf-8")))
        inventory = self.base_dir / "research" / "kfc_tuning_candidates_2026-09-25.json"
        if inventory.is_file():
            payload = json.loads(inventory.read_text(encoding="utf-8"))
            for candidate in payload.get("candidates", []):
                items.append({
                    "label": candidate["id"],
                    "category": candidate["category"],
                    "target_resource": candidate["target_resource"],
                    "target_field": candidate["target_field"],
                    "source": "Build 1076226 KFC/reflection inventory",
                    "status": candidate["status"],
                    "application_mode": candidate["application_mode"],
                    "restart_required": True,
                })
        return items
    def migrate_profile(self, profile: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
        migrated = json.loads(json.dumps(profile)); migrated.setdefault("enabled_modules", {}); migrated.setdefault("module_settings", {}); mapping = {}
        for d in self.definitions():
            module, key = d.id.split(".", 1); source = migrated["module_settings"].setdefault(module, {})
            if key in source: mapping[d.id] = d.legacy_key
            else: source[key] = d.profile_default
        migrated["registry_version"] = 2; migrated["legacy_mapping"] = mapping; return migrated, mapping
    def export_schema(self) -> list[dict[str, Any]]: return [asdict(d) for d in self.definitions()]
    def search(self, query: str, status: str | None = None) -> list[SettingDefinition]:
        needle = query.strip().lower(); items = [d for d in self.definitions() if not status or d.validation_state == status]
        return items if not needle else [d for d in items if needle in " ".join((d.id, d.label, d.description, d.category, d.subcategory, *d.tags)).lower()]
    def duplicate_targets(self) -> dict[str, list[str]]:
        targets: dict[str, list[str]] = {}
        for d in self.definitions():
            if d.target_resource: targets.setdefault(d.target_resource, []).append(d.id)
        return {key: value for key, value in targets.items() if len(value) > 1}

    def inventory_mapping(self) -> list[dict[str, Any]]:
        """Complete audit artifact: one row per legacy module/key."""
        duplicates = self.duplicate_targets()
        rows = []
        for definition in self.definitions():
            conflicts = [resource for resource, ids in duplicates.items() if definition.id in ids]
            rows.append({"legacy_module": definition.id.split(".", 1)[0], "legacy_key": definition.id.split(".", 1)[1], "stable_id": definition.id, "category": definition.category, "subcategory": definition.subcategory, "tags": list(definition.tags), "target_resource": definition.target_resource, "conflicting_targets": conflicts, "mapping_confidence": "high" if definition.subcategory and definition.target_resource else "review"})
        return rows
