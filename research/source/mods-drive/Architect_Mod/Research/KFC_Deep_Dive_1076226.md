# Enshrouded KFC Deep Dive — build 1076226

Date: 2026-09-25  
Scope: the read-only `ENSHROUDED KFC FILES` corpus, the installed `enshrouded.kfc`/`enshrouded.kfc_resources`, and the matching reflection database.

## Executive conclusion

The KFC files expose a large portion of Enshrouded's authored data model, but they do not constitute a general-purpose live configuration API. The corpus contains 131 resource families. The matching reflection database is build-scoped to revision `1076226` and describes roughly 14,000 reflected types, including field names, primitive types, array/reference kinds, offsets, enums, editor attributes, and converter names.

The most actionable control surfaces for the current project are:

1. `GameSettings` through the named admin action/event route. This is the clearest runtime-authoritative candidate because the schema contains the aggregate, `AdminChangeGameSettingsAction`, and `GameSettingsChangedEvent`.
2. Building and blueprint registries: `VoxelBlueprintConfig`, `VoxelBlueprintItemRegistryResource`, `VoxelBlueprintMaterialPoolRegistryResource`, `BuildingMaterialParametersResource`, and `BuildingMaterialBlendingResource`.
3. Item and recipe data: `ItemInfo`, `ItemRegistryResource`, `RecipeRegistryResource`, `LootableItemsResource`, and `DefaultInventoryResource`.
4. Glider and camera resource families: `GliderConfig` and `CameraStatesOverrideConfig`.
5. Terrain and environment resources: `TerraformingEfficiencyRegistryResource`, voxel/world material resources, water, weather, and fog.

The least safe assumption is that a field is writable merely because it is reflected, has an editor label, appears in a JSON export, or is visible in a KFC archive. The current evidence classifies most resource edits as reload candidates or unresolved, not live controls.

## What a KFC archive actually contains

The supplied files are ZIP archives named after resource/type families. Their entries are unnamed numeric/GUID-like files, generally represented by the project tooling as JSON exports. The archive is therefore a resource dump, not a set of hand-authored configuration files with stable filenames.

The reflection data supplies the schema needed to interpret those entries. Important schema concepts are:

- `STRUCT`: a concrete object with named fields and offsets.
- `ENUM` and `BITMASK`: constrained values or flag combinations.
- `OBJECT_REFERENCE`: a link to another resource/object, not the object contents itself.
- `BLOB_ARRAY`/`DS_ARRAY`: serialized arrays whose contents require the correct decoder.
- editor attributes such as `hidden`, `editable`, `enable_on`, `converter`, and `new_types`.
- `keen::ds::*` forms: data/serialized-side variants of many runtime types; they are related but should not be assumed to be interchangeable.

The archive filename identifies a family. The entry identity and cross-resource references determine which concrete record is being used. Any mod workflow must preserve those identities and references.

## Control map

| Area | KFC families | What the schema clearly describes | Practical control status |
|---|---|---|---|
| Game rules | `GameSettingsPresetsResource`, `IngameTimeConfig` | Player vitals, durability, starvation, food duration, shroud time, glider turbulence, weather frequency, fishing difficulty, mining, growth, drops, production, perks, XP, enemy/boss factors, aggro, pacification, day/night durations, curse modifier | `GameSettings` is the strongest live candidate; dispatch/readback still must converge. Other config resources are reload/unknown. |
| Building | `VoxelBlueprintConfig`, `VoxelBlueprintItemRegistryResource`, `VoxelBlueprintMaterialPoolRegistryResource`, `TerraformingEfficiencyRegistryResource` | Blueprint snapping rules, item geometry/relationships, material pools, terrain/building efficiency configurations | Strong static coverage. Safe catalog/preview work is plausible; world mutation and placement authority remain separate problems. |
| Building materials | `BuildingMaterialParametersResource`, `BuildingMaterialBlendingResource`, `GiVoxelBuildingMaterialResource`, `WorldMaterialBlending2Resource`, `SimpleWorldMaterialResource` | Material parameters, visual layer blending, voxel/world material properties | Good visual/material candidates; durability, collision, placement, and save behavior require independent tests. |
| Items | `ItemInfo`, `ItemRegistryResource`, `DefaultInventoryResource` | Stack sizes, rarity generation, names/descriptions, categories, equipment, damage/armor/fuel/block/scaled-cost setups, icons, perks, growth, fishing, comfort, permission data | Very broad static surface. Runtime ownership and persistence vary by consumer. |
| Crafting/progression | `RecipeRegistryResource`, `SkillTreeResource`, `Perk`, `PerkCollectionResource`, `BalancingTable` | Recipe inputs/outputs, skill nodes/links, perks and balance data | Static records are present; unlocking, progression authority, and multiplayer behavior are not established. |
| Combat/AI | `BaseAttributeResource`, `AttributeContainerResource`, `BuffType`, `EnemyArsenalRegistryResource`, `DevEnemyArsenalRegistryResource`, `ImpactProgram` | Attributes, buffs, enemy loadouts, impacts and reactions | Potentially powerful but high risk. Must correlate a record to an authoritative entity action before changing anything. |
| Movement/camera | `GliderConfig`, `CameraStatesOverrideConfig`, `CameraStatesManager` | Glider acceleration/resistance/yaw/pitch/roll/updraft threshold; camera-state overrides | Good low-world-risk research candidates; likely reload/state-transition dependent. |
| World/environment | `WeatherSystemResource`, `RenderWeatherResource`, `VolumetricFog3Resource`, `VoxelWorldFog3Resource`, water families, `VoxelTemperatureResource` | Weather, fog, water, temperature, visual environment | Mostly visual/simulation resource candidates. Do not equate fog resources with shroud-of-war authority. |
| Loot | `LootableItemsResource`, `SceneRandomLootResource`, `TrashLootTableResource`, `DefaultLootLabelCollectionResource` | Loot entries, labels, stack ranges, rarity/category filters, scene/random loot | Promising for controlled experiments; broad progression effects make this higher risk. |
| Audio/visual | sound, MIDI, voice, VFX, render model/material/texture families | Asset selection and presentation parameters | Usually presentation-only; not a route to gameplay authority. |
| Templates/entities | `TemplateResource`, `TemplateCollectionResource`, `SceneEntityChunkResource`, `SceneResource` | Entity composition, components, culling/replication flags, scenes/chunks | High impact and high risk. Template edits can change entity construction, but do not imply safe save/network behavior. |

## Highest-value reflected fields

### `keen::ecs::GameSettings`

The reflected aggregate is 144 bytes with 37 fields. Its fields are:

`playerHealthFactor`, `playerManaFactor`, `playerStaminaFactor`, `playerBodyHeatFactor`, `playerDivingTimeFactor`, `enableDurability`, `enableStarvingDebuff`, `foodBuffDurationFactor`, `fromHungerToStarving`, `shroudTimeFactor`, `tombstoneMode`, `enableGliderTurbulences`, `weatherFrequency`, `fishingDifficulty`, `miningDamageFactor`, `plantGrowthSpeedFactor`, `resourceDropStackAmountFactor`, `factoryProductionSpeedFactor`, `perkUpgradeRecyclingFactor`, `perkCostFactor`, `experienceCombatFactor`, `experienceMiningFactor`, `experienceExplorationQuestsFactor`, `randomSpawnerAmount`, `aggroPoolAmount`, `enemyDamageFactor`, `enemyHealthFactor`, `enemyStaminaFactor`, `enemyPerceptionRangeFactor`, `bossDamageFactor`, `bossHealthFactor`, `threatBonus`, `pacifyAllEnemies`, `tamingStartleRepercussion`, `dayTimeDuration`, `nightTimeDuration`, and `curseModifier`.

The same schema exposes `AdminChangeGameSettingsAction` containing the aggregate plus version data, and `GameSettingsChangedEvent` carrying the new settings. This is materially stronger evidence than a standalone resource because it indicates an intended authoritative change path. It still needs a complete producer, dispatcher, event, readback, consumer, and exact-revert chain.

### `keen::GliderConfig`

This is a compact eight-float structure: forward acceleration; longitudinal, lateral, and vertical air resistance; yaw, pitch, and roll angular speeds; and the updraft-strength charge start value. The aggregate game settings also has a separate turbulence toggle. Therefore “glider physics” and “glider turbulence” are distinct control surfaces.

### Building/terraforming

`TerraformingEfficiencyRegistryResource` contains terrain and building configuration collections. The supplied building ingestion already resolved 112 terrain configurations, 86 building configurations, 141 blueprint records, 258 material-layer records, 249 material-feedback resources, and 31 normalized snap-rule families across seven `VoxelBlueprintConfig` families. This is the best-supported KFC domain in the current project.

The evidence supports cataloging and relationship analysis. It does not yet prove that changing a registry entry changes an already-running world, that a new entry can be loaded safely, or that a placement commit will be accepted by the authoritative server.

### `keen::ds::ItemInfo`

The serialized item record is large (2,592 bytes in the current reflection) and includes identity, max stack size, rarity behavior, localization references, category, equipment setup, damage/armor/fuel/block/scaled-cost setups, icon/model data, knowledge generation, tags, perks, item level range, growth, fishing, comfort, and permission-related data. This explains why the item family is a major modding surface but also why a single item edit can fan out into UI, crafting, combat, loot, save, and network behavior.

## What is confirmed versus inferred

Confirmed from local evidence:

- The installed build and reflection data are revision-scoped; the reflection version identifies `1076226` and branch `ea_update_08`.
- 131 named KFC families are present in the supplied corpus.
- The building-focused ingestion has resolved concrete item, registry, recipe, blueprint, terrain, material, feedback, and snap relationships.
- The reflection database contains named fields, offsets, enums, references, and converter/editor metadata.
- `GameSettings` has named action/event types in the schema.

Inferred but not yet proven:

- A reflected field can be changed live without a reload.
- A resource archive can be replaced and loaded by the current executable without reindexing or cache invalidation.
- A client-side change is accepted by the host/server.
- A change persists through save/restart or propagates to other players.
- A resource-level change affects all consumers of the same record.
- A visual resource changes gameplay semantics.

## Recommended research order

1. Recover the complete `GameSettings` action/event/readback chain with one orthogonal field and exact restoration.
2. Identify the concrete camera/glider resource identities and test fresh state transitions or reload boundaries.
3. Continue the building catalog work using known item/blueprint/material identities; keep preview/catalog controls separate from commit authority.
4. Test terraforming efficiency with measured work/time outputs while leaving terrain state unchanged until the resource relationship is proven.
5. Correlate one item, recipe, loot, attribute, and buff record at a time to an independently observable action.
6. Treat template, scene, entity-chunk, animation, and broad loot edits as late-stage research because their failure modes include construction, replication, persistence, and progression damage.

## Safe validation protocol

For every candidate, fingerprint the build and source archive, capture the baseline identity/value, make one controlled vanilla action or state transition, correlate the candidate record to an independent result, repeat with a second value, test the expected refresh boundary, restore the exact original, and verify exact readback. A missing authoritative owner, ambiguous identity, cache-only result, partial equality, rejected dispatch, or uncertain persistence keeps the candidate unavailable for implementation.

## Bottom line for the current project

The KFC files give the project a very strong static knowledge base and a particularly useful building/item/game-settings map. They can tell us what the engine knows how to represent. They cannot, by themselves, tell us what the running game will permit a mod to change. The next productive milestone is not “edit every reflected field”; it is to establish a small number of verified control paths with stable identity, refresh semantics, authoritative readback, and exact revert.

Evidence used: local KFC corpus; installed `enshrouded.kfc` and `enshrouded.kfc_resources`; build-matched `reflection_data.json`; `BuildingKfcIngestion-1076226.md`; and `KFC_ModHub_Candidate_Catalog_2026-09-24.md`.
