# CODE-0042B — Registry expansion / binding-progress audit

Date: 2026-09-20
Game build scope: Enshrouded 1076226
Baseline: Architect Toolkit 0.42.0 / INC-0062
Status: SOURCE-AUDITED / PARTIAL CODE-0042B / NO RUNTIME CLAIM

## Confirmed
- `admin_action_registry.json` now contains 40 canonical actions: 17 enabled, 23 disabled/planned.
- All 22 literal `Send-CheatCommand` action IDs statically observed in `ArchitectRuntime.ps1` are represented in the registry.
- `Register-AdminActionEvent` exists and routes through `Bind-AdminActionControl` before `Register-SafeUiEvent`.
- Two real canonical bindings exist in Developer & Diagnostics:
  - `cheatcorrelation.begin`
  - `cheatcorrelation.status`
- Source Map / external source consolidation and the 224-entry CT catalog remain preserved.
- Prohibited direct PowerShell/F7 mutation calls remain absent for `TogglePatch`, `EnableAllSurvival`, `DisableAllSurvival`, `WritePlayerCoordinates`, `ToggleAutoLoot`, and `ToggleGliderFlight`.
- Teleport, Auto Loot, Glider Flight, and glider-stamina semantic restrictions remain fail-closed in current metadata/dispatch policy.

## Remaining blocker — executable-control binding coverage
`Bind-AdminActionControl` is only reached through the two Developer & Diagnostics `Register-AdminActionEvent` call sites. The rest of the legacy Admin pages still register action controls through raw `Register-SafeUiEvent`, direct `Add_Click`, or dynamic closures.

Static renderer inspection shows many legacy handlers remain outside canonical binding. Examples include Player Vitals, Mobility & Navigation, Inventory/Items, Crafting/Progression, Combat & AI, World/Camera, Building/Entities, Dashboard/Home, and Settings/Dev.

The next pass should not expand gameplay functionality. It should make every F7 control that can dispatch or request a gameplay/admin action explicitly bind to exactly one canonical ActionId. Pure UI controls such as navigation, search/filter, list selection, grid sorting, and view switching should remain UI-only and must not be forced into the gameplay action registry.

## Registry quality
The newly added action entries sampled for movement, vitals, survival, time, item reroll, parry, and glider stamina remain disabled where current evidence is insufficient. This is consistent with the project fail-closed policy.

## Related navigation cleanup
The canonical navigation array uses `Home`, but startup still calls `Show-AdminPage "Dashboard"`, which falls through to the default dashboard renderer. Normalize startup to `Show-AdminPage "Home"` during a safe UI-only cleanup.

## Acceptance target for next pass
- Every F7 gameplay/admin executable control is bound via canonical ActionId.
- Every bound ActionId resolves to one registry entry.
- No gameplay/admin action control relies only on closure text for identity.
- UI-only controls are explicitly distinguishable from action controls.
- No action is enabled merely to satisfy binding coverage.
- Existing 53/53 truthfulness and 28/28 UI smoke baselines remain green or are strengthened without weakening assertions.
- 224-entry CT catalog remains intact.
- No prohibited direct mutation fallback reappears.
