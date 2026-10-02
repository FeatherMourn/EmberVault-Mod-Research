# Architect Toolkit — F7 Admin Console Program Plan

Date: 2026-09-17
Game build scope: Enshrouded 0.9.1.2 / revision 1076226 / Hotfix #42
Product direction: F7 is Architect's built-in admin / cheat / developer console. F8 remains BUILD / CREATE / DESIGN.

## Product Goal

Build a large, evidence-driven in-game administration surface that combines trainer-style controls, vanilla game-setting overrides, world/admin tools, entity inspection, diagnostics, and developer utilities without requiring Cheat Engine during normal use.

External mods and Cheat Engine tables are capability/evidence sources only. Their offsets, patches, scripts, and assumptions are not current-build proof. Architect independently validates every runtime mechanism for revision 1076226 before enabling it.

## UX Contract

Every F7 control carries:
- support/evidence state: PROVEN / INFERRED / EXPERIMENTAL / UNSOLVED / PLANNED / DISPROVEN
- runtime behavior: LIVE / SESSION / RELOAD / UNAVAILABLE
- authority: LOCAL / HOST / SERVER / UNKNOWN
- risk: READ_ONLY / REVERSIBLE_RUNTIME / SAVE_AFFECTING / WORLD_MUTATION / EXPERIMENTAL_NATIVE
- current value where readable
- vanilla/default value where known
- readback result after mutation
- revert-to-vanilla support where practical

Unsupported controls remain visible but disabled. No command reports `completed` solely because a write was attempted.

## Canonical F7 Sections

1. Dashboard / Quick Cheats
2. Player
3. Movement & Travel
4. Inventory & Items
5. Crafting & Progression
6. Combat & Enemy AI
7. World & Game Settings
8. Map & Wayfinder
9. Camera & Cinematic
10. Glider & Physics
11. Building Admin
12. Terrain & Props
13. Entity Inspector / Spawner
14. Multiplayer Admin
15. Quest / World Progression
16. Developer / Diagnostics
17. Presets / Restore Vanilla

## Architecture

F7 UI -> AdminAction Registry -> Command Bridge -> Adapter -> Validated Enshrouded mechanism -> Readback -> Result

Primary adapters:
- PlayerAdapter
- MovementAdapter
- TravelAdapter
- InventoryAdapter
- ItemAdapter
- CraftingAdapter
- ProgressionAdapter
- CombatAdapter
- AIAdapter
- GameSettingsAdapter
- WorldAdapter
- MapAdapter
- CameraAdapter
- GliderAdapter
- BuildingAdminAdapter
- TerrainAdapter
- PropAdapter
- EntityAdapter
- MultiplayerAdminAdapter
- QuestAdapter
- DiagnosticsAdapter

Each build-specific native constant/signature remains centralized in a build profile rather than embedded in feature logic.

## Command Families / Target Capability Set

### Dashboard / Presets
- admin.preset.vanilla
- admin.preset.creative_builder
- admin.preset.explorer
- admin.preset.relaxed_survival
- admin.preset.developer
- admin.restore_vanilla
- admin.revert_last

### Player
- player.inspect
- player.health.fill / set / max / infinite / recovery
- player.stamina.fill / set / max / infinite / recovery / cost_multiplier
- player.mana.fill / set / max / infinite / recovery / cost_multiplier
- player.invulnerable
- player.revive
- player.status.cleanse
- player.fall_damage
- player.oxygen / breath
- player.shroud_time
- player.body_heat
- player.rested
- player.durability_loss
- player.attributes.*

### Movement & Travel
- movement.walk_speed
- movement.run_speed
- movement.sprint_speed
- movement.swim_speed
- movement.jump_height
- movement.gravity
- movement.flight
- movement.noclip
- movement.hover
- movement.vertical_speed
- travel.position
- travel.teleport.coordinates
- travel.teleport.marker
- travel.teleport.home
- travel.teleport.altar
- travel.return_previous
- travel.waypoint.save / delete / teleport

### Inventory & Items
- inventory.inspect
- inventory.give
- inventory.remove
- inventory.clear
- inventory.repair_all
- inventory.sort
- item.inspect
- item.amount
- item.replace
- item.level
- item.durability
- item.repair
- item.reroll
- item.upgrades.unlock
- item.duplicate
- item.delete
- item.browser.search

### Crafting & Progression
- crafting.free
- crafting.instant
- crafting.anywhere
- crafting.ignore_station
- crafting.unlock_recipes
- crafting.production_speed
- progression.level
- progression.xp
- progression.xp_multiplier
- progression.skill_points
- progression.reset_skills
- progression.unlock_skills
- progression.recipe_unlocks
- progression.station_unlocks

### Combat & Enemy AI
- combat.player_damage_multiplier
- combat.enemy_damage_multiplier
- combat.crit_rate
- combat.attack_speed
- combat.parry_window
- combat.knockback
- enemy.health_multiplier
- enemy.stamina_multiplier
- enemy.freeze_ai
- enemy.disable_aggro
- enemy.perception
- enemy.attack_frequency
- enemy.kill.radius
- enemy.despawn.radius
- boss.health_multiplier
- boss.damage_multiplier

### World & Game Settings
- world.time.get / set / pause
- world.day_length
- world.night_length
- world.plant_growth
- world.production_speed
- world.resource_yield
- world.mining_yield
- world.loot_multiplier
- world.enemy_health
- world.enemy_damage
- world.boss_health
- world.boss_damage
- world.survival.*
- world.fog_density
- world.fog_distance
- world.shroud_visuals
- world.weather.* where independently mapped

### Map & Wayfinder
- map.coordinates
- map.reveal
- map.fog_of_war
- map.locations.reveal
- map.fast_travel.unlock
- map.marker.create / delete
- map.teleport_marker

### Camera / Cinematic
- camera.free
- camera.first_person
- camera.fov
- camera.distance
- camera.offset
- camera.speed
- camera.freeze
- camera.hide_hud
- camera.saved_viewpoint.*
- cinematic.slow_motion where safely supported

### Glider & Physics
- glider.speed
- glider.acceleration
- glider.lift
- glider.drag
- glider.pitch
- glider.yaw
- glider.roll
- glider.stamina_cost
- physics.gravity_multiplier
- physics.fall_speed_limit

### Building Admin
- building.free
- building.no_material_cost
- building.ignore_build_zone
- building.build_in_shroud
- building.altar_radius
- building.altar_limit
- building.place_range
- building.instant_dismantle
- building.collision_restrictions where safely mapped
- building.debug_bounds

### Terrain & Props
- terrain.inspect
- terrain.material
- terrain.hardness
- terrain.mining_power
- terrain.flatten / fill / remove (advanced, save-affecting)
- prop.inspect
- prop.move
- prop.rotate
- prop.nudge
- prop.clone
- prop.delete
- prop.collision where supported

### Entity Inspector / Spawner
- entity.inspect.crosshair
- entity.components
- entity.transform
- entity.owner
- entity.network_authority
- entity.health
- entity.teleport_to
- entity.freeze
- entity.heal
- entity.kill
- entity.despawn
- entity.spawn (advanced)
- entity.copy_id

### Multiplayer Admin
- multiplayer.session.inspect
- multiplayer.players.list
- multiplayer.player.inspect
- multiplayer.teleport_to
- multiplayer.summon
- multiplayer.heal / revive
- multiplayer.permissions
- multiplayer.kick / ban only if supported by legitimate authority path

### Quest / World Progression
- quest.inspect
- quest.objective.inspect
- quest.start / complete / reset only after save-safe validation
- world_progression.inspect
- unlock operations only after authoritative state/readback is mapped

### Developer / Diagnostics
- diagnostics.build
- diagnostics.signatures
- diagnostics.adapters
- diagnostics.command_history
- diagnostics.last_action
- diagnostics.runtime_state
- diagnostics.entity_under_crosshair
- diagnostics.resource_id
- diagnostics.capture.*
- diagnostics.restore_hooks

## Implementation Phases

### Phase A — Foundation: Registry + Generic F7 Renderer
Goal: Build the admin console once.

Deliverables:
- AdminAction schema/registry
- data-driven toggle/slider/number/dropdown/button/read-only controls
- search/filter + command palette
- evidence/status badges
- LIVE/SESSION/RELOAD state
- authority/risk indicators
- standard readback/result contract
- revert-to-vanilla contract
- disabled placeholder entries for planned commands

Gate: existing F7/F8/bridge behavior must regress cleanly.

### Phase B — Low-Risk GameSettings Quick Wins
Goal: Turn resource-backed/current-build vanilla settings into working controls before solving harder entity memory ownership.

Targets:
- day/night lengths
- player/enemy/boss multipliers where exposed
- resource/mining/loot multipliers
- production and plant growth
- survival timers/multipliers
- fog/shroud visuals
- glider settings
- selected building-area restrictions/settings

Method: REUSE -> EXTEND -> COMPOSE first. Determine LIVE vs SESSION vs RELOAD independently for each setting.

### Phase C — Player Runtime Adapter
Goal: validated local-player identity and live vital state.

Dependencies:
- CODE-0022A runtime gate revalidation
- CODE-0022B multi-signal discovery harness

Targets:
- health/stamina/mana readback
- first reversible mutation only after read path is proven
- invulnerability/regen/cost multipliers later

### Phase D — Movement / Travel / Camera
Goal: core trainer-quality mobility/admin workflows.

Targets:
- coordinates
- speed/jump/gravity
- flight/hover/noclip
- waypoints/teleport
- camera/freecam/FOV
- map marker integration

### Phase E — Inventory / Items / Crafting / Progression
Goal: robust item/admin editor.

Targets:
- item browser/inspector
- give/remove/amount/repair
- level/reroll/upgrades
- free/instant crafting
- recipe/progression controls

Safety: save-affecting actions require readback and test-world validation.

### Phase F — Combat / AI / World Administration
Goal: live encounter/world tuning.

Targets:
- damage multipliers
- enemy/boss multipliers
- AI freeze/aggression/perception
- time/weather/world controls
- cleanup utilities

### Phase G — Building Admin / Terrain / Prop Editing
Goal: advanced world-authoring/admin tools beyond normal F8 building workflow.

Targets:
- building restriction overrides
- altar/build areas
- terrain admin
- prop inspect/move/rotate/clone/delete
- collision/debug overlays

F8 remains creative building. F7 provides authority/admin overrides and inspector tooling.

### Phase H — Entity Inspector / Spawner
Goal: make F7 useful as an internal reverse-engineering and developer console.

Priority feature: crosshair entity inspector showing identity, resource/type, transform, owner/network authority, components and available validated actions.

Spawner is enabled only after resource/entity creation paths are independently validated.

### Phase I — Multiplayer / Quest / Save-Affecting Advanced Admin
Goal: host/server-authoritative and destructive operations.

This is last by default because authority and save integrity requirements are highest.

Requirements:
- explicit Advanced Admin mode
- test-world recommendation
- authority validation
- compatibility/build checks
- backup/snapshot where technically practical
- audit/history
- fail-closed on mismatch

## Parallel Workstreams

Workstream 1: F7 Registry/UI framework (CODE-0023)
Workstream 2: Player runtime discovery (CODE-0022B)
Workstream 3: GameSettings/resource research and live-refresh mapping
Workstream 4: Entity inspector foundations
Workstream 5: capability-map/static research for Inventory, Movement, Camera, Map and Building Admin

These streams should converge into common adapters/registry instead of creating standalone trainer implementations.

## Prioritization Rule

Within each phase prefer features with:
1. existing vanilla/resource mechanism
2. deterministic readback
3. reversible/session-only state
4. low save/world corruption risk
5. high user utility

Defer features requiring unknown ownership, unsafe arbitrary memory writes, multiplayer authority guesses, or irreversible world/save mutation.

## Evidence Promotion

- External tool demonstrates feature: EXTERNAL EVIDENCE only.
- Current static layout/reference found: INFERRED or PROVEN_STATIC_BUILD_1076226 as appropriate.
- Architect captures current runtime state consistently: EXPERIMENTAL -> PROVEN read path when validated.
- Architect mutation succeeds once: still EXPERIMENTAL.
- Mutation succeeds with authoritative readback, repeated lifecycle tests, and clean revert/unload: candidate for PROVEN_BUILD_1076226.

## Product Completion Definition

F7 reaches the intended product shape when:
- registry-driven UI exposes the full capability catalog
- common high-value trainer controls are independently validated and live
- unavailable features clearly show why they are unavailable
- a user can administer player, movement, inventory, crafting, world, camera, building and diagnostics without Cheat Engine for supported functions
- advanced world/save/multiplayer operations are isolated and explicitly gated
- game updates fail closed and only affected adapters need remapping

