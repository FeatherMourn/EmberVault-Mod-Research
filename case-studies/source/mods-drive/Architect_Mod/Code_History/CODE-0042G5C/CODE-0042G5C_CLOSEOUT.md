# CODE-0042G5C — Mobility Responsive Closeout

Date: 2026-09-21
Build: Enshrouded 1076226

Status: CLOSED_OFFLINE_SOURCE_STATIC / GAMEPLAY_RUNTIME_UNPROVEN

Authoritative file:
`I:\My Drive\Enshrouded Mods\Architect_Mod\Current\runtime\ArchitectRuntime.ps1`

Verified final source identity:
- Length: 382655 bytes
- SHA-256: `0E856F05E1B079C5528B14783CB5C93391B962CDB650B4BC2D590D4B5DFDAC90`

User-reported G5C results:
- Runtime before: `05BCD81A...C0D76E`
- Runtime after: `0E856F05...FDAC90`
- Home hash unchanged
- Player hash unchanged
- Mobility hash changed as intended
- G5C Mobility parity: 31/31 PASS
- Player parity: 18/18 PASS
- Truthfulness: 72/72 PASS
- UI smoke: 30/30 PASS
- UI errors: 0
- PowerShell parse: PASS
- Lifecycle/static/G4A: PASS
- Source consolidation/schema: 12/12 PASS
- CT catalog: 224
- Registry: 55 total / 17 enabled / 38 disabled / 55 unique
- Mobility raw direct event registrations: 0
- Stable-definition Control refs: 0
- Stable-definition Handler refs: 0
- Prohibited mutation scan: PASS
- Geometry: `SKIPPED_NO_WINFORMS_LAYOUT_HARNESS`

Responsive architecture:
- responsive cards for header, locomotion, glider, teleport sections
- percentage-column `New-F7ResponsiveTable` layouts
- Dock-filled controls and stretched location list
- responsive filter/search/safe-elevation/coordinate/action rows
- no invalid Absolute row-height objects

Product source changed:
- `runtime/ArchitectRuntime.ps1`

Explicit boundaries:
- registry unchanged
- native code unchanged
- Lua/EML unchanged
- Home unchanged
- Player unchanged
- unrelated pages unchanged
- H: not recreated
- G5D/F8 not started
- no gameplay/runtime mechanism changed or proven
