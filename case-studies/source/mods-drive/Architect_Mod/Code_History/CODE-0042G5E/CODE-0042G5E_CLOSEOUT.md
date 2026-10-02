# CODE-0042G5E — Combat & AI Responsive Closeout

Date: 2026-09-21
Build: Enshrouded 1076226

Status: CLOSED_OFFLINE_SOURCE_STATIC / GAMEPLAY_RUNTIME_UNPROVEN

Authoritative file:
`I:\My Drive\Enshrouded Mods\Architect_Mod\Current\runtime\ArchitectRuntime.ps1`

Verified final source identity:
- Length: 434597 bytes
- SHA-256: `06FA6C846F5E2B5CD3DDA838AB7F1A8C2875FFBE3DB87C773BB7F5F36BCD23D2`

Verified registry identity:
- Length: 60272 bytes
- SHA-256: `7F2F5C38B75AF24B45728D5D6B6FBD5A9420BE51BF52888DD008AE77B0E21AA8`

User-reported G5E results:
- Runtime before: `8CEBE9F8...B762228`
- Runtime after: `06FA6C84...CD23D2`
- Home unchanged
- Player unchanged
- Mobility unchanged
- Inventory unchanged
- Crafting/Progression unchanged
- World unchanged
- Combat changed as intended
- G5E parity: 40 requirement groups PASS
- Player parity: 18/18 PASS
- Mobility parity: 31/31 PASS
- Items/Progression parity: 46 requirement groups PASS
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
- Combat header, player multipliers, and AI controls use responsive cards/tables
- damage, critical, AI, boss-health, and boss-damage groups use percentage columns
- long unsupported controls stretch within table cells
- row labels and values use separate responsive rows to avoid WinForms layout collisions
- no invalid Absolute row-height objects

TEMP-only verification changes reported:
- added G5E Combat parity fixture
- adapted verification as needed for the responsive source structure
- UI smoke overlap regression was fixed inside `Render-CombatAIPage`
- no semantic safety assertions weakened

Product source changed:
- `runtime/ArchitectRuntime.ps1`

Explicit boundaries:
- registry unchanged
- native code unchanged
- Lua/EML unchanged
- backend unchanged
- dispatch unchanged
- other page renderers unchanged
- H: not recreated
- G5F/World & Environment not started
- F8 not started
- no gameplay/runtime mechanism changed or proven
