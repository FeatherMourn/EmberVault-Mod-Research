# CODE-0042G5F — Autonomous goal package

Date: 2026-09-21
Build: Enshrouded 1076226

Purpose:
Autonomous milestone goal for responsive migration of the shared F7 `Render-WorldCameraPage`.

Authoritative starting source:
`I:\My Drive\Enshrouded Mods\Architect_Mod\Current\runtime\ArchitectRuntime.ps1`

Verified starting identity:
- Length: 434597 bytes
- SHA-256: `06FA6C846F5E2B5CD3DDA838AB7F1A8C2875FFBE3DB87C773BB7F5F36BCD23D2`

Verified registry baseline:
- SHA-256: `7F2F5C38B75AF24B45728D5D6B6FBD5A9420BE51BF52888DD008AE77B0E21AA8`
- 55 total / 17 enabled / 38 disabled / 55 unique

Current source facts:
- `Render-WorldCameraPage` remains fixed-pixel.
- Both `World & Environment` and `Camera & Presentation` dispatch to `Render-WorldCameraPage`.
- `Render-WorldBuildingPage` also delegates to `Render-WorldCameraPage`.
- G2D previously source-closed World/Camera event migration with three canonical source registration sites and zero raw direct event sites.
- Canonical actions:
  - `world.time_of_day`
  - `cheat.world.plant_growth`
  - `world.time_pause`
- All three remain registry-disabled / UNSOLVED / backend NONE.
- Direct dispatch remains explicitly fail-closed with `WORLD_TIME_UNSOLVED`, `WORLD_TIME_PAUSE_UNSOLVED`, and `PLANT_GROWTH_UNSOLVED`.
- Resource Yield, Loot Drop, Freecam/Flycam, Hide HUD, FOV, and Timescale remain disabled/unbound placeholders.

Closed responsive baselines to preserve:
- G5B Player
- G5C Mobility
- G5D Items & Progression
- G5E Combat & AI

This goal gives Codex autonomous permission to iterate inside `Render-WorldCameraPage` and TEMP-only verification infrastructure, returning only for genuine product/safety blockers.
