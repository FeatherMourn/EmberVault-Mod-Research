# CODE-0042G5G — Autonomous goal package

Date: 2026-09-21
Build: Enshrouded 1076226

Purpose:
Autonomous milestone goal for responsive migration of F7 `Render-BuildingEntitiesPage`, used by `Building & World Editing`.

Authoritative starting source:
`I:\My Drive\Enshrouded Mods\Architect_Mod\Current\runtime\ArchitectRuntime.ps1`

Verified starting identity:
- Length: 442662 bytes
- SHA-256: `C56F388AC295A0998BB53E00E7910F40D45EE69DD878263A8B4B02D3299EF64E`

Verified registry baseline:
- SHA-256: `7F2F5C38B75AF24B45728D5D6B6FBD5A9420BE51BF52888DD008AE77B0E21AA8`
- 55 total / 17 enabled / 38 disabled / 55 unique

Current source/evidence facts:
- `Building & World Editing` dispatches to `Render-BuildingEntitiesPage`.
- `Render-BuildingEntitiesPage` is still fixed-pixel at G5G start.
- G2E source-closed the renderer's direct-event migration:
  - raw `Register-SafeUiEvent` = 0
  - raw `.Add_Click` = 0
  - exactly three canonical action registration sites
- Canonical building actions:
  - `f7.building.altarArea.toggle.click` -> `cheat.world.altar_area`
  - `f7.building.altarFar.toggle.click` -> `cheat.world.altar_far`
  - `f7.building.buildRange.toggle.click` -> `cheat.world.build_range`
- All three remain registry-disabled / UNSOLVED / backend NONE / runtime UNAVAILABLE.
- Direct dispatch remains fail-closed with:
  - `ALTAR_AREA_UNSOLVED`
  - `ALTAR_FAR_UNSOLVED`
  - `BUILD_RANGE_UNSOLVED`
- Dismantle, terrain, prop, and entity mutation controls remain disabled and handler-free.
- The renderer calls `Get-EntityInspectorState`; inspector semantics are outside this responsive milestone and must not be changed.

Closed responsive baselines to preserve:
- G5B Player
- G5C Mobility
- G5D Items & Progression
- G5E Combat & AI
- G5F World & Environment

This goal gives Codex autonomous permission to iterate inside `Render-BuildingEntitiesPage` and TEMP-only verification infrastructure, returning only for genuine product/safety blockers.
