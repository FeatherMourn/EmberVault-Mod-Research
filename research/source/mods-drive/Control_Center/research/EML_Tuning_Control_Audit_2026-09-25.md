# Control Center / EML tuning-control audit

Date: 2026-09-25  
Game build context: reflection/KFC revision `1076226`  
Scope: `I:\My Drive\Enshrouded Mods\Control_Center`, its generated EML Lua loader, module manifests/patches, active profile, and the local KFC/reflection research.

## Bottom line

The Control Center currently has a broad tuning catalog, but the EML implementation presently provides one demonstrated mechanism:

```lua
game.assets.get_resources_by_type(typeName)
```

The generated loader wraps that as `context.GetResources`, then modules mutate fields on returned Lua-visible resource objects, usually during `OnInit`. There is no confirmed generic EML API in this project for:

- dispatching the game's authoritative ECS/admin actions;
- publishing a changed event;
- committing a resource back to KFC or a save file;
- synchronizing a client-side mutation to the host/server;
- forcing resource reload/reindex;
- applying profile changes live after startup.

Therefore the reliable classification is:

- `IMPLEMENTED AS EML STARTUP PATCH`: the module locates a resource and writes a field in Lua.
- `STATIC/UNVERIFIED`: the field/resource is named and may be reachable, but the project has not proven the game consumes the mutation.
- `UI/PROFILE ONLY`: Control Center exposes the setting, but the current patch does not implement it.
- `LIVE UNSUPPORTED`: the project’s live IPC file exists, but no module currently implements a real live update path; the only explicit `OnLiveConfigUpdate` is a reserved stub.

## What EML is actually doing in this project

`runtime/master_loader.lua` is generated from the profile. It builds a `Brain` object with logging, resource lookup, two generic Lua tables (`Player` and `GameRules`), and module initialization. The generic setters are:

```lua
SetPlayerAttribute = function(k, v) if _G.Player then _G.Player[k] = v end
SetGlobalRule = function(k, v) if _G.GameRules then _G.GameRules[k] = v end
```

Those are table assignments, not known engine-authority calls. The useful path is resource lookup plus mutation of the returned resource object's `.data` table.

`runtime/live_config.json` is written by the desktop application, but the generated loader does not show a file watcher or a live-config polling loop. `architect_companion` defines `OnLiveConfigUpdate`, but its body is only `-- Reserved for live IPC`. All module manifests have empty live-setting lists. In practical terms, changing the UI/profile after launch should be treated as startup-only until a loader log and in-game readback prove otherwise.

## Current tuning surface by module

| Module | Intended settings | Current EML implementation | Assessment |
|---|---|---|---|
| `survival_qol` | stack multiplier, shroud time, infinite durability, stamina drain reduction | Mutates `ItemInfo.maxStackSize`; one hard-coded `BalancingTable.playerBaseFogResistance`; `GameSettingsPresetsResource` min/max values; optional `FbUiBundle` difficulty values | `ItemInfo` stack changes are the clearest implemented path. Shroud and GameSettings changes are unverified; UI bundle mutation is not proof of authoritative game settings. |
| `world_and_difficulty` | enemy/boss factors, pacify, XP, mining, growth, production, durability, food duration | Targets preset/UI resources, but the patch writes only selected UI/game-setting-shaped values and must be inspected per field | Strongest intended vanilla-tuning module, but not equivalent to live/server-authoritative `GameSettings`. |
| `progression_balancing` | caps, base health/stamina/mana, skill/AP rates, crits, altar limits | Writes fields on every `BalancingTable` found | Broad static mutation surface; field names are plausible but runtime ownership and persistence are unproven. |
| `architect_companion` | freecam, camera FOV, altar radius, restrictions | Writes `BalancingTable` altar sizes/counts; the camera and live hook are not implemented in the shown patch | Altar radius/count is a startup table mutation. Freecam/FOV/restriction controls are UI/profile claims unless another native hook exists. |
| `inventory_and_items` | max stacks, durability, weapon damage, glider speed, grapple range | Looks up `ItemInfo`; only fields actually assigned in the patch can be considered implemented | Item-level changes are plausible; generic durability/weapon/glider/grapple multipliers are not automatically mapped to KFC fields. |
| `crafting_and_recipes` | craft speed, ingredient discount, yield, master recipes | Looks up `RecipeRegistryResource`; recipe edits are possible only where patch code maps concrete recipe fields | Registry access is real; production speed belongs elsewhere, and “inject” requires valid record creation/reference handling. |
| `skills_and_perks` | skill discount, perk damage | Looks up `SkillTreeResource` and `Perk` | Static records are reachable; unlock/cost/damage authority is unresolved. |
| `building_and_architecture` | building cost, altar radius | Looks up `BuildingMaterialParametersResource` and `BalancingTable` | Material/resource mutation is possible as a startup patch; placement authority and save/network behavior remain unproven. |
| `starter_loadout` | starter boost, glider hook, potions, runes | Looks up default-inventory resource variants | Potentially controls defaults/new-character inventory, not existing character inventory unless a separate runtime path exists. |
| `buffs_and_status` | lifetime, death persistence, food poisoning | Looks up `BuffType`/`BaseAttributeResource`; explicit buff death flag mutation exists | Good static buff surface; existing active buffs may require reapplication and authoritative ownership. |
| `environment_time_weather` | night illumination, rain saturation, death-screen desaturation | Looks up ambient post-processing/parameter resources | Visual effects are plausible; time-of-day/weather gameplay authority is not established. |
| `loot_and_chests` | legendary rate, trash fishing probability | Looks up loot and fishing trash tables | Good candidate for controlled startup experiments; loot generation timing and server ownership matter. |
| `terraforming_and_mining` | terraforming speed | Looks up `TerraformingEfficiencyRegistryResource` | Strong static candidate; needs action-level measured readback. |
| `music_and_instruments` | instrument comfort, volume | Looks up instrument and balancing resources | Presentation/comfort fields may be reachable; effect ownership is not proven. |
| `knowledge_and_map` | knowledge points, recipe knowledge unlock | Looks up knowledge/journal/item-knowledge resources | Resource presence is real; player progression state is likely separate from definitions. |
| `custom_*` modules | new or modified furniture, weapons, spells, blocks, pets, farming, art, music, hair, colors, gliders | Mostly attempts to use `ItemInfo`, `RecipeRegistryResource`, or preset collections | These are content/resource experiments, not proven gameplay tuning controls. New records need valid IDs, references, registries, icons, recipes, and consumer support. |

## Vanilla GameSettings controls available in the KFC schema

The build-matched reflection exposes `keen::ecs::GameSettings` with 37 fields:

`playerHealthFactor`, `playerManaFactor`, `playerStaminaFactor`, `playerBodyHeatFactor`, `playerDivingTimeFactor`, `enableDurability`, `enableStarvingDebuff`, `foodBuffDurationFactor`, `fromHungerToStarving`, `shroudTimeFactor`, `tombstoneMode`, `enableGliderTurbulences`, `weatherFrequency`, `fishingDifficulty`, `miningDamageFactor`, `plantGrowthSpeedFactor`, `resourceDropStackAmountFactor`, `factoryProductionSpeedFactor`, `perkUpgradeRecyclingFactor`, `perkCostFactor`, `experienceCombatFactor`, `experienceMiningFactor`, `experienceExplorationQuestsFactor`, `randomSpawnerAmount`, `aggroPoolAmount`, `enemyDamageFactor`, `enemyHealthFactor`, `enemyStaminaFactor`, `enemyPerceptionRangeFactor`, `bossDamageFactor`, `bossHealthFactor`, `threatBonus`, `pacifyAllEnemies`, `tamingStartleRepercussion`, `dayTimeDuration`, `nightTimeDuration`, and `curseModifier`.

The same reflection data exposes `AdminChangeGameSettingsAction` and `GameSettingsChangedEvent`. That is the preferred future route for authoritative tuning. The current EML loader does not call that route; it edits `GameSettingsPresetsResource` and/or `FbUiBundle` tables instead. Those should be treated as preset/UI-definition mutations until an in-game settings readback confirms they affect the active world.

## High-confidence control categories

### Best current candidates

- Item definition fields such as `ItemInfo.maxStackSize`, where the module explicitly retrieves items and assigns the field.
- Balancing-table scalar/array fields explicitly assigned by `progression_balancing` and `architect_companion`.
- Buff definition fields explicitly assigned by `buffs_and_status`.
- Recipe, loot, fishing, terraforming, and default-inventory records when the patch maps a concrete field rather than merely listing a target resource.

### Usable after targeted validation

- `GameSettingsPresetsResource` values for durability, stamina, enemy factors, XP, mining, growth, factory production, food duration, and related settings.
- `TerraformingEfficiencyRegistryResource` efficiency values.
- `CameraStatesOverrideConfig` and glider-related definitions.
- `BuildingMaterialParametersResource`, blueprint snapping, and material registries.

### Not established by the current EML bridge

- Live post-startup changes from Control Center.
- Existing-player health/mana/stamina changes through profile values.
- Fast travel, fog-of-war, building-area authority, placement restrictions, or save mutation.
- Multiplayer-safe changes from a client.
- Exact persistence across world restart.
- Generic creation of new engine resources from Lua.

## Important implementation mismatches

Several Control Center settings are broader than their current engine mapping. Examples:

- `glider_speed_multiplier` is a profile setting, but the KFC reflection shows glider physics in `GliderConfig`, not a generic `ItemInfo` multiplier.
- `grapple_range_multiplier` has no demonstrated KFC field mapping in the audited code.
- `craft_speed_multiplier` is not the same thing as `factoryProductionSpeedFactor`; one concerns recipe/workbench timing, the other is a GameSettings field.
- `player_base_health`, `player_base_stamina`, and `player_base_mana` are balancing-table candidates, while `playerHealthFactor`, `playerStaminaFactor`, and `playerManaFactor` are GameSettings multipliers. They affect different layers.
- `shroud_time_multiplier` and `shroud_fog_resistance_multiplier` both target fog-related behavior but through different concepts; they should not be merged without an action-level test.
- `enable_freecam`, `camera_fov`, and `ignore_building_restrictions` are not demonstrated by the current `architect_companion` patch body.
- `unlock_all_recipe_knowledge` concerns knowledge/definition resources, not necessarily the player’s saved unlock state.

## Recommended EML research plan

1. Add a loader capability/readback probe that logs, for each target type, resource count, GUID, field existence, old value, new value, and whether the assignment survives a fresh gameplay action.
2. Establish one known-good `ItemInfo.maxStackSize` experiment and one known-good `BalancingTable` scalar experiment. Record the effect, refresh boundary, save behavior, and revert.
3. Build a dedicated `GameSettings` probe. Locate the active settings object, compare it with preset/UI resources, and determine whether the active world consumes preset edits or requires `AdminChangeGameSettingsAction`.
4. Implement a real live-update contract only after proving the EML side has a file watcher or callback path. Until then, label all settings startup-only in the UI.
5. Separate definitions from player/world state in the registry. A resource edit should not be presented as changing an existing character, existing terrain, or existing save unless readback proves it.
6. Gate every setting by evidence state: `resource_found`, `field_found`, `assignment_succeeded`, `behavior_changed`, `persisted`, `reverted`, and `multiplayer_verified`.

## Final assessment

Control Center is currently strongest as a startup resource-patching and profile-management tool. It has a credible foundation for item, balancing, buff, recipe, loot, terraforming, and material experiments. It is not yet a verified live game-settings controller through EML. The next high-value engineering task is a readback/authority probe around `GameSettings`, followed by accurate UI labeling so intended controls are not presented as confirmed controls.

Evidence reviewed: `runtime/master_loader.lua`, `runtime/live_config.json`, all module manifests and Lua patches, `profiles/active_profile.json`, `core/module.schema.json`, the local KFC corpus, the build-matched reflection data, and prior KFC/runtime research notes.
