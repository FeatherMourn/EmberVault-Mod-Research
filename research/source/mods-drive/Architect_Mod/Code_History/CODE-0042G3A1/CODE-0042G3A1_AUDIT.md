# CODE-0042G3A1 — Missing preset-ID fail-closed presentation audit

Date: 2026-09-21
Build scope: Enshrouded 1076226
ArchitectRuntime.ps1 SHA-256: 5cfa316d1985f83cd4b404c83ead1af4b3be68b2f58aeb1a4f61b641a7ec38db
admin_action_registry.json SHA-256: 7f2f5c38b75af24b45728d5d6b6fbd5a9420be51bf52888dd008ae77b0e21aa8
Registry actions: 55
Enabled: 17
Disabled: 38
Status: SOURCE-VERIFIED G3A CLOSED / OFFLINE TESTS USER-CODEX-REPORTED / NO RUNTIME CLAIM

## Source-verified G3A1

`Render-RolePresetsPage` now handles malformed preset IDs fail-closed.

For a blank/missing preset id:

- no event is registered;
- no fallback EventId is generated;
- no ActionId is invented;
- the Apply button is explicitly disabled;
- disabled styling is applied;
- tooltip and `AccessibleDescription` both report:
  `Preset unavailable: stable preset id is missing.`

Valid presets remain unchanged:

`f7.presets.apply.<presetId>.click -> admin.preset.apply`

Custom preset save remains:

`f7.presets.save.click`

and refreshes with:

`Clear-AdminContent`
then
`Render-RolePresetsPage`

Shared preset execution remains fail-closed in both:

- `Invoke-ArchitectPreset`
- `Send-CheatCommand "admin.preset.apply"`

Registry remains 55 actions / 17 enabled / 38 disabled.

## Test provenance

Reported by user/Codex:

- malformed-preset static assertion: PASS
- Role Presets raw `.Add_Click`: 0
- Role Presets raw `Register-SafeUiEvent`: 0
- real registry import: 55 unique
- PowerShell parse: PASS
- lifecycle fixture: PASS
- F7 truthfulness: 53/53 PASS
- UI smoke: 28/28 PASS
- UI errors: 0
- CT catalog: 224
- schema/adaptor validation: PASS
- G1/G2 raw closure preserved
- prohibited mutation scan: clean

The temporary lifecycle fixture remains in the user's reconstructed local workspace and is not independently source-audited from Drive in this pass.

## G3B source inventory — Settings / Developer

`Render-SettingsDevPage` currently has exactly 5 raw `.Add_Click(...)` sites:

1. Role Presets subnav
2. Native Diagnostics subnav
3. Panic Reset
4. Save Keybindings
5. Apply Preferences

Classification:

- Role Presets subnav -> UI_ONLY
- Native Diagnostics subnav -> UI_ONLY
- Panic Reset -> ACTION -> `cheat.survival.disable_all`
- Save Keybindings -> UI_ONLY local configuration persistence
- Apply Preferences -> UI_ONLY local configuration persistence

The active `HOTKEYS` subtab button has no handler and should remain presentation-only for the current view.

## Panic Reset truthfulness issue

Current raw Panic Reset handler does:

`Send-CheatCommand "cheat.survival.disable_all"`

then unconditionally reports:

`EMERGENCY PANIC: Reset all patches to Vanilla.`

But the canonical action `cheat.survival.disable_all` is disabled / `UNSOLVED` / backend `NONE` / runtime `UNAVAILABLE`, and `Send-CheatCommand` already fails closed for this action.

G3B must canonicalize the button and make the handler report success only when the command result actually succeeds. A rejected command must show the returned failure and must not claim vanilla restoration.

No new backend or registry change is required.
