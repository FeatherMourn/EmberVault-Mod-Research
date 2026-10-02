# Enshrouded Mod Hub — KFC candidate catalog (2026-09-24)

Status: research note; non-canonical; build-scoped to 1076226 unless noted.

## Scope and evidence boundary

Reviewed the canonical Project Index and Research Index, the current Project Control/GameSettings records, the existing GameSettings static reports and dispatch/readback negative results, the current Mod Hub/F7 manifests, and the read-only `ENSHROUDED KFC FILES` corpus. KFC archives were treated as static resource evidence only. No KFC file was modified, renamed, moved, or deleted. No retired-project artifact was changed.

Authority order used: user/runtime evidence > runtime captures/tests > current source > structured state > static analysis > KFC/resource evidence > research/planning. This catalog does not claim that a reflected field, resource, or archive is runtime-writable.

## Executive result

No new KFC field is presently `LIVE`, `SESSION`, or `RELOAD` capable in Mod Hub. The best candidates are:

1. `GameSettings` aggregate fields, via the named vanilla action/event route, if dispatch and authoritative readback can be recovered.
2. `GliderConfig` and `CameraStatesOverrideConfig`, if resource identity, load/override, and refresh semantics can be mapped.
3. `TerraformingEfficiencyRegistryResource` and voxel/building material resources, if a safe pre-placement/resource path can be distinguished from world mutation.
4. `BaseAttributeResource`, if its records can be correlated to a known server-authoritative attribute consumer without broad memory scanning.

## Prioritized candidate catalog

| Priority | Candidate / KFC family | Static candidate | Current classification | Why it matters | First discriminating test |
|---|---|---|---|---|---|
| P0 | `GameSettings` aggregate: health/mana/stamina, durability, plant growth, production, XP, enemy/boss factors, day/night durations, glider turbulence | Reflected `keen::ecs::GameSettings` size `0x90`; named `AdminChangeGameSettingsAction` and `GameSettingsChangedEvent`; fields previously mapped at offsets `0x00`–`0x88` | `PROVEN_STATIC_BUILD_1076226`; `CANDIDATE_LIVE`; supported mode `UNAVAILABLE` | Highest UX value and closest match to existing game-tuning manifests | Observe-only recovery of action producer/dispatcher plus event/query readback. On a private host, capture the full aggregate/version, submit one orthogonal change through the legitimate route, require exact changed-event/readback equality, test one consumer, then restore the captured aggregate and verify exact equality. Stop on any missing authority/readback.
| P1 | `GliderConfig` | Reflected config shape includes acceleration, resistance axes, yaw/pitch/roll speeds, and updraft charge threshold; aggregate also has turbulence toggle | `PROVEN_STATIC_RESOURCE_SHAPE`; `RELOAD_CANDIDATE`; supported `UNAVAILABLE` | Directly extends existing glider tuning work without conflating residual stamina drain with flight physics | Identify resource GUID/registry entry and loaded instance in an observe-only session. Compare config before/after entering/exiting glider state; verify whether a new flight reads values live or only after world/session reload. No write until serialization and independent behavioral readback exist.
| P1 | `CameraStatesOverrideConfig` / `CameraStatesManager` | Dedicated camera override resource family is present in KFC; current research already treats camera as a subsystem | `PROVEN_STATIC_RESOURCE_FAMILY`; `RELOAD_CANDIDATE`; supported `UNAVAILABLE` | Low world/save risk; good first resource scalar family after prior FOV non-convergence | Enumerate camera-state transitions (exploration, aiming, building, gliding), capture active state identity and camera outputs, and correlate one config field at a time to a new transition. Require stable identity, no pointer guessing, and revert by leaving/re-entering the state.
| P2 | `TerraformingEfficiencyRegistryResource` | Dedicated registry resource is present; terrain research family already identified | `PROVEN_STATIC_RESOURCE_SHAPE`; `RELOAD_CANDIDATE`; supported `UNAVAILABLE` | Could expose material/tool efficiency rather than persistent terrain mutation | In a test world, capture material/tool/action tuple and observed work amount/time for two vanilla materials. Map the registry record used by the action, then test whether a session reload changes a fresh action while existing terrain remains untouched. Do not edit terrain or resource files.
| P2 | `VoxelBlueprintConfig`, `VoxelBlueprintItemRegistryResource`, `VoxelBlueprintMaterialPoolRegistryResource` | Dedicated blueprint/item/material-pool resources; building ingestion and carrier path already exist | `PROVEN_STATIC_RESOURCE_FAMILY`; `RELOAD_CANDIDATE`; world mutation `UNSOLVED` | Strongest route for expanding Architect’s proven single-carrier catalog and material UX | Observe startup selection and Construction Hammer registration for one known carrier. Correlate item/resource identity, shape/material record, and preview/placement behavior. Test catalog-only additions or selection changes in a disposable session; do not infer commit authority from preview or late `BuildingPlaceEvent` fields.
| P3 | `BuildingMaterialParametersResource` / `BuildingMaterialBlendingResource` | Dedicated material parameter/blending archives | `PROVEN_STATIC_RESOURCE_FAMILY`; `RELOAD_CANDIDATE` | May support visual/behavioral material presets and blending without changing placement authority | Place two vanilla materials, capture surface/visual/structural outputs, then map the resource records consumed by fresh previews. Separate visual blending from durability, collision, and save semantics. No write until each effect has independent readback.
| P3 | `BaseAttributeResource`, `AttributeContainerResource`, `BuffType` | Attribute and buff resource families are present; GameSettings has player vitals multipliers | `PROVEN_STATIC_RESOURCE_FAMILY`; runtime ownership `UNSOLVED` | Possible bridge between static tuning and server-authoritative player/AI attributes | Use phase-marked observe-only captures for idle, damage, heal, stamina drain/recovery, mana spend/recovery, and one buff apply/remove. Correlate stable entity/attribute identity and event timing; reject generic registry-only matches.
| P3 | `IngameTimeConfig` plus `dayTimeDuration`/`nightTimeDuration` | Dedicated tiny config archive plus aggregate duration fields | `PROVEN_STATIC_RESOURCE/AGGREGATE`; live clock authority `UNSOLVED` | Separates clock configuration from clock position, which is currently unsolved | Capture clock value/phase over a bounded interval, then test only a fresh session/world change after a validated aggregate action or config route. Do not claim time-of-day control from duration fields.
| P4 | `VolumetricFog3Resource`, `VoxelWorldFog3Resource` | Fog resources expose visual parameters/materials; current static report identifies extinction, height, camera fade, barrier thickness/noise | `PROVEN_STATIC_RESOURCE_SHAPE`; `RELOAD_CANDIDATE`; supported `UNAVAILABLE` | Useful visual QoL, but not fog-of-war, shroud timer, or travel authority | Capture camera/world region and fog output across a controlled boundary; correlate resource identity and visual-only changes. Explicitly test that gameplay shroud damage/time does not change before treating it as a separate visual feature.
| P4 | `TrashLootTableResource`, `BalancingTable`, `WorkshopRegistryResource` | Loot/balancing/workshop resource families are present | `PROVEN_STATIC_RESOURCE_FAMILY`; semantic ownership `UNSOLVED` | Potential loot/drop and workshop tuning, but broad and high-risk for progression | First map one concrete vanilla action (fresh trash/container loot or workshop production) to a record and independent result. Require host/session scope, deterministic test inputs, and full revert. Do not generalize one table to all loot or crafting.

## Candidates explicitly not promoted

- Recipe unlocking, item/level caps, skill points per level, global spell costs/cast time, fast travel, fog of war, building area limits, and building restrictions remain `UNSOLVED` or `UNAVAILABLE`.
- Resource presence is not a supported override route. The project’s current data-index notes that the raw installed KFC archives do not yet have a project-verified decoder preserving resource identity.
- Unique static signatures, reflected layouts, compilation, or a UI control do not establish runtime authority, refresh, persistence, multiplayer ownership, or safe revert.

## Shared validation protocol

For every candidate: fingerprint build and executable; install no mutation; capture baseline identity and value; perform one controlled vanilla action/state transition; correlate the candidate record to an independently observable effect; repeat with a second value or orthogonal control; test session/world transition; restore the original; require exact readback; unload cleanly. Any build mismatch, ambiguous owner, missing event/query, partial equality, cache-only effect, authority rejection, or persistence ambiguity leaves the candidate `UNAVAILABLE`.

## Recommended next research sprint

Run one bounded observe-only session that prioritizes P0 action/event recovery and P1 camera/glider resource identity. If P0 still fails to converge, preserve the negative result and proceed with the least risky P1 resource identity test; do not broaden into raw scanning or enable mutation. The first implementation target should be whichever candidate demonstrates stable owner, refresh, independent readback, and exact revert in the same build.

## Evidence pointers

- Canonical Project Index: `Enshrouded Mods — Project Index`.
- Research navigation: `Architect — Research Index`.
- Existing static aggregate analysis: `GameSettings-CODE-0023-Static.md`.
- Existing negative dispatch/readback result: `GameSettings-CODE-0024-Dispatch-Readback.md` and `GameSettings-CODE-0025-DataFlow.md`.
- Existing KFC/building context: `BuildingKfcIngestion-1076226.md`.
- Read-only corpus: `ENSHROUDED KFC FILES`.
- Current Mod Hub baseline: F7/Architect manifests and Project Control rows for GameSettings/backend state.
