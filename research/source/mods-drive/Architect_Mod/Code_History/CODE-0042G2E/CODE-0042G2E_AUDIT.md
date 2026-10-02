# CODE-0042G2E — Building / Entities event migration audit

Date: 2026-09-21
Build scope: Enshrouded 1076226
ArchitectRuntime.ps1 SHA-256: 9a397f2b7dd0e1a5829beb5b0d3725beeac7fc6f87b2032fc8316975c5d30cd7
admin_action_registry.json SHA-256: 7f2f5c38b75af24b45728d5d6b6fbd5a9420be51bf52888dd008ae77b0e21aa8
Registry actions: 55
Enabled: 17
Disabled: 38
Status: SOURCE-VERIFIED G2 CLOSURE / OFFLINE TESTS USER-CODEX-REPORTED / NO RUNTIME CLAIM

## Source-verified G2E

`Render-BuildingEntitiesPage` now has:

- raw `Register-SafeUiEvent`: 0
- raw `.Add_Click(...)`: 0

Canonical Building EventIds:

- `f7.building.altarArea.toggle.click` -> `cheat.world.altar_area`
- `f7.building.altarFar.toggle.click` -> `cheat.world.altar_far`
- `f7.building.buildRange.toggle.click` -> `cheat.world.build_range`

All three actions remain disabled / `UNSOLVED` / backend `NONE` / runtime `UNAVAILABLE` / unknown authority / mutation risk.

`Send-CheatCommand` explicitly rejects before native publication:

- `build.altar_area` / `cheat.world.altar_area` -> `ALTAR_AREA_UNSOLVED`
- `build.altar_far` / `cheat.world.altar_far` -> `ALTAR_FAR_UNSOLVED`
- `cheat.world.build_range` -> `BUILD_RANGE_UNSOLVED`

Terrain, prop, dismantle, and entity mutation controls remain disabled and handler-free.

## Bounded G2 closure

Source-level raw event counts are now zero for:

- Inventory / Items
- Crafting / Progression
- Combat / AI
- World / Camera
- Building / Entities

G1 Home / Player / Mobility / shell closure also remains intact.

Therefore the bounded G2 event migration is source/offline closed.

This does not establish in-game/runtime behavior.

## Test provenance

Reported by user/Codex:

- real registry import: 55 unique
- lifecycle fixture: PASS
- PowerShell parse: PASS
- F7 truthfulness: 53/53 PASS
- UI smoke: 28/28 PASS
- UI errors: 0
- CT catalog: 224
- schema/adaptor validation: PASS
- prohibited mutation scan: clean

The temporary lifecycle fixture remains in the user's reconstructed local workspace and is not independently source-audited from Drive in this pass.

## G3 raw-event inventory

Remaining F7 source-level direct registrations are concentrated in the non-G1/G2 subviews/dialogs:

- `Render-RolePresetsPage`: 2 `.Add_Click`
- `Render-SettingsDevPage`: 5 `.Add_Click`
- `Render-MultiplayerQuestsPage`: 4 `.Add_Click`
- `Update-CodexDetails`: 4 `.Add_Click`
- `Render-CodexWikiPage`: 5 `Register-SafeUiEvent`
- `Update-WaypointDetails`: 1 `.Add_Click` plus 1 direct `.Add_TextChanged`
- `Render-MapWayfinderPage`: 3 `Register-SafeUiEvent` + 6 `.Add_Click`
- `Show-BlueprintBrowser`: 3 `Register-SafeUiEvent` + 4 `.Add_Click` + 1 direct `.Add_KeyDown`
- `Show-AdminMenu`: 1 direct `.Add_KeyDown` + 1 direct `.Add_FormClosing`

Important audit limitation:
`Get-F7DirectEventAudit` currently counts only `Register-SafeUiEvent` and `.Add_Click(...)`, and its function list does not include several helper/dialog functions above. Full-F7 zero-gap closure must eventually broaden the audit to all direct `.Add_<Event>(...)` registrations and all F7-owned helper/dialog functions.

## Recommended G3 sequence

- G3A — Role Presets
- G3B — Settings / Developer
- G3C — Multiplayer / Quests
- G3D — Codex
- G3E — Map / Wayfinder
- G3F — Blueprint Browser + remaining F7 dialog/shell helpers
- G4 — full-F7 comprehensive direct-event audit + repeated traversal + responsive layout migration

Responsive layout work remains deferred until G3 event closure.
