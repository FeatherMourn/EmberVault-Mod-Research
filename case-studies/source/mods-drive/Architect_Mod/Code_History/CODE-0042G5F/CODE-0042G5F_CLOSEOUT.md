# CODE-0042G5F — World & Environment Responsive Closeout

Date: 2026-09-21
Build: Enshrouded 1076226

Status: CLOSED_OFFLINE_SOURCE_STATIC / GAMEPLAY_RUNTIME_UNPROVEN

Authoritative file:
`I:\My Drive\Enshrouded Mods\Architect_Mod\Current\runtime\ArchitectRuntime.ps1`

Verified final source identity:
- Length: 442662 bytes
- SHA-256: `C56F388AC295A0998BB53E00E7910F40D45EE69DD878263A8B4B02D3299EF64E`

Verified starting/source-history identity:
- Prior G5E runtime length: 434597 bytes
- Prior G5E SHA-256: `06FA6C846F5E2B5CD3DDA838AB7F1A8C2875FFBE3DB87C773BB7F5F36BCD23D2`

Verified registry identity:
- Length: 60272 bytes
- SHA-256: `7F2F5C38B75AF24B45728D5D6B6FBD5A9420BE51BF52888DD008AE77B0E21AA8`

Independent source-diff verification:
- `Render-WorldCameraPage` changed between G5E and G5F as intended.
- `Render-DashboardPage` unchanged.
- `Render-PlayerVitalsPage` unchanged.
- `Render-MobilityTravelPage` unchanged.
- `Render-InventoryItemsPage` unchanged.
- `Render-CraftingProgressionPage` unchanged.
- `Render-CombatAIPage` unchanged.
- `Render-BuildingEntitiesPage` unchanged.
- `Render-MultiplayerQuestsPage` unchanged.

User-reported G5F results:
- G5F parity fixture: PASS
- Player parity: 18/18 PASS
- Mobility parity: 31/31 PASS
- Items/Progression parity: 46 groups PASS
- Combat parity: 40 groups PASS
- Truthfulness: 72/72 PASS
- UI smoke: 30/30 PASS
- UI errors: 0
- Lifecycle/static: PASS
- Source consolidation: 12/12 PASS
- CT catalog: 224
- Registry/schema checks: PASS
- Prohibited mutation scan: PASS
- World raw direct events: 0
- World canonical registration source sites: 3
- Geometry: `SKIPPED_NO_WINFORMS_LAYOUT_HARNESS`

Responsive architecture:
- `Render-WorldCameraPage` now uses `New-F7ResponsiveCard` and `New-F7ResponsiveTable`.
- World/time and camera sections use percentage-column layouts.
- Unsupported controls remain disabled and unbound.
- World-time, pause, and plant-growth fail-closed semantics remain preserved.
- Shared routing remains conceptually unchanged: World & Environment and Camera & Presentation continue to use the shared World/Camera renderer; `Render-WorldBuildingPage` remains its wrapper.

TEMP-only verification:
- added `test_g5f_world_camera_parity.ps1`
- no gameplay/runtime proof was inferred from static/source checks

Product source changed:
- `runtime/ArchitectRuntime.ps1`

Explicit boundaries:
- registry unchanged
- native code unchanged
- Lua/EML unchanged
- backend/dispatch unchanged
- protected renderers unchanged
- H: not recreated
- G5G not started
- F8 not started
- no gameplay/runtime mechanism changed or proven
