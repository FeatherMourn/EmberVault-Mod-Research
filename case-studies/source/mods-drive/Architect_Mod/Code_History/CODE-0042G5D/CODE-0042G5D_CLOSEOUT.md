# CODE-0042G5D — Items & Progression Responsive Closeout

Date: 2026-09-21
Build: Enshrouded 1076226

Status: CLOSED_OFFLINE_SOURCE_STATIC / GAMEPLAY_RUNTIME_UNPROVEN

Authoritative file:
`I:\My Drive\Enshrouded Mods\Architect_Mod\Current\runtime\ArchitectRuntime.ps1`

Verified final source identity:
- Length: 396725 bytes
- SHA-256: `8CEBE9F8B3C273005A433031399663C130187AA92B5BDFDEA8FE50905B762228`

Verified registry identity:
- Length: 60272 bytes
- SHA-256: `7F2F5C38B75AF24B45728D5D6B6FBD5A9420BE51BF52888DD008AE77B0E21AA8`

User-reported G5D results:
- Runtime before: `0E856F05...FDAC90`
- Runtime after: `8CEBE9F8...B762228`
- Home hash unchanged
- Player hash unchanged
- Mobility hash unchanged
- Inventory renderer changed as intended
- Crafting/Progression renderer changed as intended
- Combat hash unchanged
- G5D parity: 46 requirement groups PASS
- Player parity: 18/18 PASS
- Mobility parity: 31/31 PASS
- Truthfulness: 72/72 PASS
- UI smoke: 30/30 PASS
- UI errors: 0
- PowerShell parse: PASS
- Lifecycle/static/G4A: PASS
- Source consolidation/schema: 12/12 PASS
- CT catalog: 224
- Registry: 55 total / 17 enabled / 38 disabled / 55 unique
- Prohibited mutation scan: PASS
- Stable-definition Control refs: 0
- Stable-definition Handler refs: 0
- Geometry: `SKIPPED_NO_WINFORMS_LAYOUT_HARNESS`

Responsive architecture:
- responsive cards and percentage-column tables across Inventory and Progression
- responsive Codex category/search/quantity controls
- horizontally stretched item list
- responsive unsupported action groups
- responsive skill input/apply/reset controls and presets
- responsive level/XP/crafting controls
- no invalid Absolute row-height objects
- page dispatcher order preserved: `Render-InventoryItemsPage; Render-CraftingProgressionPage`
- `Render-ProgressionGearPage` still delegates to `Render-CraftingProgressionPage`

TEMP-only verification changes reported:
- added G5D Items/Progression parity fixture
- adapted lifecycle checks to active renderer ASTs and current preset-variable naming
- no semantic safety assertions weakened

Product source changed:
- `runtime/ArchitectRuntime.ps1`

Explicit boundaries:
- registry unchanged
- native code unchanged
- Lua/EML unchanged
- Home unchanged
- Player unchanged
- Mobility unchanged
- Combat unchanged
- backend/dispatch logic unchanged
- H: not recreated
- G5E/Combat not started
- F8 not started
- no gameplay/runtime mechanism changed or proven
