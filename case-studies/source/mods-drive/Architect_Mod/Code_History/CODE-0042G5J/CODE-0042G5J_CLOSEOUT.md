# CODE-0042G5J — Developer & Diagnostics Responsive Closeout

Date: 2026-09-21
Build: Enshrouded 1076226

Status: CLOSED_OFFLINE_SOURCE_STATIC / GAMEPLAY_RUNTIME_UNPROVEN

Authoritative source:
`I:\My Drive\Enshrouded Mods\Architect_Mod\Current\runtime\ArchitectRuntime.ps1`

## Independently verified final identity

- Length: 449835 bytes
- SHA-256: `D510D65A3A25FB4080DC3BC466AD9D0736661FF0E2F3F291989721437F366EF8`

Starting G5I baseline:
- Length: 448462 bytes
- SHA-256: `2CFD1FA80A0B8FF6647E0816489AD3534D78F43F264D75B9330A857DECE0751C`

Registry:
- Length: 60272 bytes
- SHA-256: `7F2F5C38B75AF24B45728D5D6B6FBD5A9420BE51BF52888DD008AE77B0E21AA8`
- 55 total / 17 enabled / 38 disabled / 55 unique command IDs

## Independent function-diff verification

Top-level named-function comparison between archived G5I and final Current shows exactly three changed functions:

- `Render-DiagnosticsPage`
- `Render-CodexWikiPage`
- `Update-CodexDetails`

Function hashes:
- `Render-DiagnosticsPage`
  - before: `BE583D36F3079940E1B12A2F129C47A3E4D642BAB8C50FB06E58862A76201A16`
  - after: `01C77E81785EE807B147457782480EB2635A54F1CE9C6D7DD1A11342986FD336`
- `Render-CodexWikiPage`
  - before: `CE52F9CCDADA70CB623FEEFCC4AF15AAE84BFDB1C13287C2C033F3D95D3A5AB9`
  - after: `26EE387C75A414D890513C9BC0C595C0D69628940AB089F50E2A3179A5DCC1C5`
- `Update-CodexDetails`
  - before: `4FE2AE9D93AD106E9C01DBDD4CCCE2A41CD4D067F90EE077C0E0CFA2F910037D`
  - after: `75BE313A0FE4EE7BEE565F8BDED63A7AFFB15F955B9073237B081F5DEC176751`

Protected functions verified source-identical:
- `Update-CodexFilter`
- `New-AdminCatalogGrid`
- `Get-ArchitectCatalogRows`
- `Render-RolePresetsPage`
- `Render-SettingsDevPage`
- Home / Player / Mobility / Inventory / Crafting-Progression / Combat / World-Camera / Building / Entities-Authority renderers

Exactly one active definition remains for each G5J target.
No `Render-DiagnosticsPageLegacy`, `Render-CodexWikiPageLegacy`, or `Update-CodexDetailsLegacy` definition exists.

## Independently source-verified responsive changes

- `Render-DiagnosticsPage` now uses responsive F7 card/table infrastructure.
- Diagnostics telemetry is docked, multiline, vertically scrollable, with a bounded minimum size and the existing Consolas/green telemetry presentation.
- ARM and REFRESH retain their canonical actions and EventIds.
- `Render-CodexWikiPage` now begins with a responsive root and preserves canonical action indexing / Codex state behavior.
- `Update-CodexDetails` preserves narrow `Codex & Commands` DETAIL binding cleanup before rebuilding details.
- Catalog/filter infrastructure remains protected and unchanged.

## User/Codex-reported regression results

- G5J parity fixture: PASS
- G5B-G5I parity suites: PASS
- Truthfulness: 72/72 PASS
- UI smoke: 30/30 PASS
- UI errors: 0
- Lifecycle/static: PASS
- Source consolidation/schema: 12/12 PASS
- CT catalog: 224
- Prohibited mutation scan: PASS
- Registry: PASS
- H installation: absent
- Geometry: `SKIPPED_NO_WINFORMS_LAYOUT_HARNESS`

## Evidence boundary

G5J is closed at source/static level only.

No diagnostic/backend/native/entity-inspector mechanism was added or modified.
No gameplay/runtime mechanism was changed or proven.
Protected catalog helpers, filtering helper, Role Presets, Settings, and earlier responsive pages remain unchanged.
H: was not recreated.
G5K was not started.
F8 was not started.

`G5J Developer & Diagnostics responsive/parity verification is closed at source/static level.`
