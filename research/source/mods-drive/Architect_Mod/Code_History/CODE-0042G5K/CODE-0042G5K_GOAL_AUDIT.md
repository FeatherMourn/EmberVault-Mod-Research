# CODE-0042G5K — Autonomous goal package

Date: 2026-09-21
Build: Enshrouded 1076226

Purpose:
Autonomous milestone goal for responsive migration of the F7 `Render-RolePresetsPage` subpage.

Authoritative starting source:
`I:\My Drive\Enshrouded Mods\Architect_Mod\Current\runtime\ArchitectRuntime.ps1`

Independently verified starting identity:
- Length: 449835 bytes
- SHA-256: `D510D65A3A25FB4080DC3BC466AD9D0736661FF0E2F3F291989721437F366EF8`

Registry baseline:
- SHA-256: `7F2F5C38B75AF24B45728D5D6B6FBD5A9420BE51BF52888DD008AE77B0E21AA8`
- 55 total / 17 enabled / 38 disabled / 55 unique

Scope:
- Product edit: `Render-RolePresetsPage` only.
- Protected helpers: `Load-ArchitectPresets`, `Save-ArchitectPresets`, `Invoke-ArchitectPreset`.
- Protected callers: Home `CUSTOMIZE PRESETS >>` and Mods & Configuration `ROLE PRESETS`.
- Protect all G5A-G5J closed responsive renderers/helpers.

Current preset truth:
- `admin.preset.apply` is disabled.
- evidenceStatus = EXPERIMENTAL.
- backend = NONE.
- runtimeMode = SESSION.
- authority = unknown.
- risk = compound_mutation.
- `Invoke-ArchitectPreset` independently refuses execution while canonical orchestration is disabled.
- G5K must not enable preset execution.

Current Role Presets semantics:
- Load presets from `Load-ArchitectPresets`.
- If empty, display four ordered built-in fallback preset definitions.
- Valid stable preset IDs bind dynamic canonical events:
  `f7.presets.apply.<presetId>.click`
  -> `admin.preset.apply`.
- Blank/missing IDs fail closed with disabled styling, truthful reason, and no event.
- Custom local preset save uses UI_ONLY `f7.presets.save.click`.
- Custom local object preserves id/name/desc/color/builtIn/cheats schema and persists through `Save-ArchitectPresets`.
- Role Presets is still fixed-pixel at G5K start.

Prior protected-function hash from the G5I/G5J lineage:
- `Render-RolePresetsPage`:
  `4F85385E794C0C487840103DEE28B390A9A3A273F093F6B1EDDF2069E55449E2`

Closed responsive baselines to preserve:
- G5A Home
- G5B Player
- G5C Mobility
- G5D Items & Progression
- G5E Combat & AI
- G5F World & Environment / Camera
- G5G Building & World Editing
- G5H Entities & Authority
- G5I Mods & Configuration
- G5J Developer & Diagnostics

G5K is UI/source-static work only. Preset gameplay execution remains unproven and fail-closed.
