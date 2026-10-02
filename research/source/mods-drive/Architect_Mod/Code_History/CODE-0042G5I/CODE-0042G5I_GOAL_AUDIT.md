# CODE-0042G5I — Autonomous goal package

Date: 2026-09-21
Build: Enshrouded 1076226

Purpose:
Autonomous milestone goal for responsive migration of F7 `Render-SettingsDevPage`, used by the `Mods & Configuration` navigation page.

Authoritative starting source:
`I:\My Drive\Enshrouded Mods\Architect_Mod\Current\runtime\ArchitectRuntime.ps1`

Independently verified starting identity:
- Length: 448538 bytes
- SHA-256: `F67E9DEA0A7549966A9118385816E1AECDE4B1ACEC3799DE0E902F48E04D3A07`

Independently verified registry baseline:
- Length: 60272 bytes
- SHA-256: `7F2F5C38B75AF24B45728D5D6B6FBD5A9420BE51BF52888DD008AE77B0E21AA8`
- 55 total / 17 enabled / 38 disabled / 55 unique

Independently extracted starting function identities:
- `Render-SettingsDevPage`:
  `678348E5FD08C34A461211B3C28EC7EA57B20C4A22CA47C6DD94D89D848A1654`
- `Render-RolePresetsPage`:
  `4F85385E794C0C487840103DEE28B390A9A3A273F093F6B1EDDF2069E55449E2`
- `Render-DiagnosticsPage`:
  `BE583D36F3079940E1B12A2F129C47A3E4D642BAB8C50FB06E58862A76201A16`

Current source facts:
- `Mods & Configuration` dispatches to `Render-SettingsDevPage`.
- `Render-SettingsDevPage` is fixed-pixel at G5I start.
- Its subnav contains HOTKEYS, ROLE PRESETS, NATIVE DIAGNOSTICS, and PANIC RESET.
- Role Presets and Native Diagnostics navigation use UI_ONLY `Register-F7UiEvent` events.
- Panic Reset uses canonical `Register-AdminActionEvent`:
  `f7.settings.panicReset.click` -> `cheat.survival.disable_all`.
- Registry truth for `cheat.survival.disable_all` is disabled / UNSOLVED / backend NONE / runtime UNAVAILABLE.
- `Send-CheatCommand` explicitly rejects both canonical and alias survival-disable-all commands with no PowerShell fallback.
- Hotkey save and preference apply are UI_ONLY `Register-F7UiEvent` actions.
- Seven hotkey binding definitions are present and must remain semantically identical.
- Immersion preferences use Architect-local `activePreferences` fields and are persisted through `Save-ArchitectKeybindings`.
- `Render-RolePresetsPage` and `Render-DiagnosticsPage` are explicitly outside G5I product-edit scope.
- G5H closeout taught that renderer parity must be active-AST/function scoped and dead legacy duplicates must not be created.

Closed responsive baselines to preserve:
- G5B Player
- G5C Mobility
- G5D Items & Progression
- G5E Combat & AI
- G5F World & Environment
- G5G Building & World Editing
- G5H Entities & Authority, repaired/closed by CODE-0042G5H1

This goal gives Codex autonomous permission to iterate only inside `Render-SettingsDevPage` and TEMP-only verification infrastructure, returning only for genuine product/safety blockers.
