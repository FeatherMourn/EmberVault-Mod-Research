# CODE-0042G5G — Building & World Editing Responsive Closeout

Date: 2026-09-21
Build: Enshrouded 1076226

Status: CLOSED_OFFLINE_SOURCE_STATIC / GAMEPLAY_RUNTIME_UNPROVEN

Authoritative file:
`I:\My Drive\Enshrouded Mods\Architect_Mod\Current\runtime\ArchitectRuntime.ps1`

Verified starting identity:
- Length: 442662 bytes
- SHA-256: `C56F388AC295A0998BB53E00E7910F40D45EE69DD878263A8B4B02D3299EF64E`

Verified final identity:
- Length: 449290 bytes
- SHA-256: `D82ECDA9A9EAAC7837B22B640235D1C4DC63FF947A88B843D06537F1DCC0BB1B`

Verified registry identity:
- Length: 60272 bytes
- SHA-256: `7F2F5C38B75AF24B45728D5D6B6FBD5A9420BE51BF52888DD008AE77B0E21AA8`

Independent protected-function comparison against archived G5F:
- `Render-DashboardPage`: unchanged
- `Render-PlayerVitalsPage`: unchanged
- `Render-MobilityTravelPage`: unchanged
- `Render-InventoryItemsPage`: unchanged
- `Render-CraftingProgressionPage`: unchanged
- `Render-CombatAIPage`: unchanged
- `Render-WorldCameraPage`: unchanged
- `Render-MultiplayerQuestsPage`: unchanged
- `Get-EntityInspectorState`: unchanged
- `Publish-EntityInspectorCommand`: unchanged
- `Render-BuildingEntitiesPage`: changed as intended

User-reported G5G results:
- G5G Building parity fixture: PASS
- Player parity: 18/18 PASS
- Mobility parity: 31/31 PASS
- Items/Progression parity: 46 groups PASS
- Combat parity: 40 groups PASS
- World/Camera parity: PASS
- Truthfulness: 72/72 PASS
- UI smoke: 30/30 PASS
- UI errors: 0
- Lifecycle/static: PASS
- Source consolidation/schema: 12/12 PASS
- CT catalog: 224
- Prohibited mutation scan: PASS
- Registry checks: PASS
- H installation: absent
- Geometry: `SKIPPED_NO_WINFORMS_LAYOUT_HARNESS`

Responsive architecture:
- `Render-BuildingEntitiesPage` now uses responsive cards/tables.
- The three canonical Building actions remain fail-closed and registry-disabled.
- Unsupported dismantle, terrain, prop, and entity mutation controls remain disabled and unbound.
- Entity Inspector fallback text and helper contracts were preserved.
- No inspector-schema concern was discovered or modified.

TEMP-only verification:
- Added `test_g5g_building_parity.ps1` in the temporary reconstructed toolkit test tree.

Product source changed:
- `runtime/ArchitectRuntime.ps1`

Explicit boundaries:
- registry unchanged
- native code unchanged
- Lua/EML unchanged
- backend/dispatch unchanged
- protected renderers unchanged
- Entity Inspector helpers unchanged
- H: not recreated
- G5H not started
- F8 not started
- no gameplay/runtime mechanism changed or proven
