# CODE-0042G1F1A — Shell closure + AdminAction schema audit

Date: 2026-09-20
Build scope: Enshrouded 1076226
Current ArchitectRuntime.ps1 SHA-256: a0e97140bde5c77a328c083adfed08f6b5813ca0cd8a45b7a7babd2c4f655397
Current admin_action_registry.json SHA-256: 698f1bed9bf4d370f778b637b55df6d7fef7f5c26e46ed73dcb1ec54664ce2a1
Registry action count: 54
Status: SHELL UI SOURCE-CLEAN / REGISTRY SCHEMA BLOCKER FOUND / NO RUNTIME CLAIM

## Shell source status

Source inspection confirms the intended G1F1A shell closure:

- `f7.shell.content.sizeChanged` is registered through `Register-F7UiEvent` with `LifetimeScope="SHELL"`.
- `Clear-AdminContent` now uses property-safe liveness checking through `Test-F7LiveBindingControl`.
- Active bindings are pruned when not live or not `SHELL`; surviving action-control maps are rebuilt from live active bindings.
- Home, Player, and Mobility page migrations remain intact.
- The AOB Scanner remains the one intentionally raw shell ACTION and still calls `NativeMemoryEngine.ToggleScanner()`.

The reported shell result is therefore credible at source level:
- shell UI-only raw registrations: 0
- shell ACTION raw registrations: 1 (AOB Scanner)

## New blocker exposed by the full runtime import

The user's full WinForms lifecycle run stopped before exercising the shell lifecycle because `Import-AdminActionRegistry` rejected `cheat.item.reroll.controlType = "action"`.

Independent validation against the preserved INC-0062 `runtime/AdminActionRegistry.psm1` shows this is not a one-row problem. The current 54-action registry has multiple enum values outside the canonical v2 schema.

### Canonical AdminAction v2 enum vocabulary

From the preserved module:

- evidenceStatus: `UNSOLVED`, `PLANNED`, `EXPERIMENTAL`, `PROVEN_BUILD_1076226`, `DISPROVEN_BUILD_1076226`
- runtimeMode: `LIVE`, `SESSION`, `RELOAD`, `UNAVAILABLE`
- controlType: `toggle`, `button`, `integer`, `float`, `slider`, `dropdown`, `read_only`
- authority: `local`, `host`, `server`, `unknown`
- backend: `LUA_API`, `VANILLA_ACTION`, `RESOURCE`, `NATIVE_OBJECT`, `NATIVE_MEMORY`, `NATIVE_HOOK`, `NONE`

The module also creates only these adapter names:
`PlayerAdapter`, `MovementAdapter`, `TravelAdapter`, `InventoryAdapter`, `CraftingAdapter`, `GameSettingsAdapter`, `WorldAdapter`, `CameraAdapter`, `GliderAdapter`, `BuildingAdminAdapter`, `MultiplayerAdminAdapter`, `DiagnosticsAdapter`

## Current schema violations

### Invalid controlType (13)
- `cheat.item.reroll` → `action`
- `cheat.skills.reset` → `action`
- `cheat.skills.set` → `numeric`
- `cheat.survival.disable_all` → `action`
- `cheat.survival.enable_all` → `action`
- `movement.jump_height` → `numeric`
- `movement.speed` → `numeric`
- `player.health.fill` → `action`
- `player.mana.fill` → `action`
- `player.stamina.fill` → `action`
- `world.time_of_day` → `numeric`
- `movement.teleport` → `action`
- `admin.preset.apply` → `action`

### Invalid evidenceStatus (13)
- `cheat.world.glider_stamina` → `SEMANTIC_MISMATCH`
- `player.health.fill` → `BUILD_GATED`
- `player.mana.fill` → `BUILD_GATED`
- `player.stamina.fill` → `BUILD_GATED`
- `world.time_of_day` → `BUILD_GATED`
- `world.time_pause` → `BUILD_GATED`
- `cheat.godmode.toggle` → `BUILD_GATED`
- `cheat.mana.toggle` → `BUILD_GATED`
- `cheat.stamina.toggle` → `BUILD_GATED`
- `cheat.freecraft.toggle` → `BUILD_GATED`
- `cheat.autoloot.toggle` → `STARTUP_CANARY_ONLY`
- `movement.teleport` → `ADM-TEST-0002`
- `admin.preset.apply` → `ORCHESTRATION_ONLY`

### Invalid runtimeMode (1)
- `cheat.autoloot.toggle` → `STARTUP`

### Invalid authority (33)
- `cheat.parry.toggle` → `native_runtime`
- `cheat.skills.reset` → `native_runtime`
- `cheat.skills.set` → `native_runtime`
- `cheat.survival.disable_all` → `native_runtime`
- `cheat.survival.enable_all` → `native_runtime`
- `cheat.world.altar_area` → `native_runtime`
- `cheat.world.altar_far` → `native_runtime`
- `cheat.world.build_range` → `native_runtime`
- `cheat.world.glider_stamina` → `none`
- `cheat.world.plant_growth` → `native_runtime`
- `movement.autorun` → `native_runtime`
- `movement.gravity` → `native_runtime`
- `movement.jump_height` → `native_runtime`
- `movement.speed` → `native_runtime`
- `player.health.fill` → `native_runtime`
- `player.mana.fill` → `native_runtime`
- `player.stamina.fill` → `native_runtime`
- `world.time_of_day` → `native_runtime`
- `world.time_pause` → `native_runtime`
- `cheat.godmode.toggle` → `native_runtime`
- `cheat.mana.toggle` → `native_runtime`
- `cheat.stamina.toggle` → `native_runtime`
- `cheat.shroud.toggle` → `native_runtime`
- `cheat.durability.toggle` → `native_runtime`
- `cheat.falldamage.toggle` → `native_runtime`
- `cheat.stealth.toggle` → `native_runtime`
- `cheat.oxygen.toggle` → `native_runtime`
- `cheat.cold.toggle` → `native_runtime`
- `cheat.freecraft.toggle` → `native_runtime`
- `cheat.autoloot.toggle` → `startup_canary`
- `movement.teleport` → `unresolved`
- `admin.preset.apply` → `native_runtime`
- `movement.position.read` → `unresolved`

### Invalid backend (29)
- `cheat.parry.toggle` → `NATIVE_CORRELATION`
- `cheat.skills.reset` → `NATIVE_CORRELATION`
- `cheat.skills.set` → `NATIVE_CORRELATION`
- `cheat.survival.disable_all` → `NATIVE_CORRELATION`
- `cheat.survival.enable_all` → `NATIVE_CORRELATION`
- `cheat.world.altar_area` → `NATIVE_CORRELATION`
- `cheat.world.altar_far` → `NATIVE_CORRELATION`
- `cheat.world.build_range` → `NATIVE_CORRELATION`
- `cheat.world.plant_growth` → `NATIVE_CORRELATION`
- `movement.autorun` → `NATIVE_CORRELATION`
- `movement.gravity` → `NATIVE_CORRELATION`
- `movement.jump_height` → `NATIVE_CORRELATION`
- `movement.speed` → `NATIVE_CORRELATION`
- `player.health.fill` → `NATIVE_CORRELATION`
- `player.mana.fill` → `NATIVE_CORRELATION`
- `player.stamina.fill` → `NATIVE_CORRELATION`
- `world.time_of_day` → `NATIVE_CORRELATION`
- `world.time_pause` → `NATIVE_CORRELATION`
- `cheat.godmode.toggle` → `NATIVE_CORRELATION`
- `cheat.mana.toggle` → `NATIVE_CORRELATION`
- `cheat.stamina.toggle` → `NATIVE_CORRELATION`
- `cheat.shroud.toggle` → `NATIVE_CORRELATION`
- `cheat.durability.toggle` → `NATIVE_CORRELATION`
- `cheat.falldamage.toggle` → `NATIVE_CORRELATION`
- `cheat.stealth.toggle` → `NATIVE_CORRELATION`
- `cheat.oxygen.toggle` → `NATIVE_CORRELATION`
- `cheat.cold.toggle` → `NATIVE_CORRELATION`
- `cheat.freecraft.toggle` → `NATIVE_CORRELATION`
- `admin.preset.apply` → `EXISTING_DISPATCH_ONLY`

### Adapter names outside the module's adapter table (34)
- `cheat.item.reroll` → `ItemAdapter`
- `cheat.parry.toggle` → `NativeCorrelationAdapter`
- `cheat.skills.reset` → `NativeCorrelationAdapter`
- `cheat.skills.set` → `NativeCorrelationAdapter`
- `cheat.survival.disable_all` → `NativeCorrelationAdapter`
- `cheat.survival.enable_all` → `NativeCorrelationAdapter`
- `cheat.world.altar_area` → `NativeCorrelationAdapter`
- `cheat.world.altar_far` → `NativeCorrelationAdapter`
- `cheat.world.build_range` → `NativeCorrelationAdapter`
- `cheat.world.glider_stamina` → `None`
- `cheat.world.plant_growth` → `NativeCorrelationAdapter`
- `movement.autorun` → `NativeCorrelationAdapter`
- `movement.gravity` → `NativeCorrelationAdapter`
- `movement.jump_height` → `NativeCorrelationAdapter`
- `movement.speed` → `NativeCorrelationAdapter`
- `player.health.fill` → `NativeCorrelationAdapter`
- `player.mana.fill` → `NativeCorrelationAdapter`
- `player.stamina.fill` → `NativeCorrelationAdapter`
- `world.time_of_day` → `NativeCorrelationAdapter`
- `world.time_pause` → `NativeCorrelationAdapter`
- `cheat.godmode.toggle` → `NativeCorrelationAdapter`
- `cheat.mana.toggle` → `NativeCorrelationAdapter`
- `cheat.stamina.toggle` → `NativeCorrelationAdapter`
- `cheat.shroud.toggle` → `NativeCorrelationAdapter`
- `cheat.durability.toggle` → `NativeCorrelationAdapter`
- `cheat.falldamage.toggle` → `NativeCorrelationAdapter`
- `cheat.stealth.toggle` → `NativeCorrelationAdapter`
- `cheat.oxygen.toggle` → `NativeCorrelationAdapter`
- `cheat.cold.toggle` → `NativeCorrelationAdapter`
- `cheat.freecraft.toggle` → `NativeCorrelationAdapter`
- `cheat.autoloot.toggle` → `StartupCanary`
- `movement.teleport` → `None`
- `admin.preset.apply` → `ArchitectPresetAdapter`
- `movement.position.read` → `None`

These adapter names are not currently rejected by `Import-AdminActionRegistry`, but they are semantically inconsistent with `New-AdminAdapterTable` and would produce `ADAPTER_UNAVAILABLE` if an action using them were ever enabled.

## Interpretation

The CODE-0042 registry expansion introduced descriptive vocabulary such as:

- `action`
- `numeric`
- `BUILD_GATED`
- `SEMANTIC_MISMATCH`
- `STARTUP_CANARY_ONLY`
- `ADM-TEST-0002`
- `ORCHESTRATION_ONLY`
- `native_runtime`
- `unresolved`
- `NATIVE_CORRELATION`
- `EXISTING_DISPATCH_ONLY`

Those labels are useful engineering notes, but they are not valid values in the canonical `architect.admin_action_registry.v2` runtime schema.

They should remain in descriptions/failure reasons/evidence notes, not in schema-enforced enum fields.

## Required next step before scanner work

Normalize all 54 rows to the existing v2 schema. Do not widen the schema or add new enum values merely to accept the expanded registry.

Required gate:
1. `Import-AdminActionRegistry` succeeds against the current 54-action registry.
2. All 54 command IDs remain unique.
3. No currently enabled action changes enablement or proven state.
4. Unsupported/unqualified actions remain disabled.
5. Domain-specific semantic labels are preserved in `description` / `failureReason` rather than schema enums.
6. The lifecycle fixture runs through the real registry import.
7. Only after registry import is green should the full shell lifecycle audit and scanner canonicalization continue.

Responsive migration remains deferred.
