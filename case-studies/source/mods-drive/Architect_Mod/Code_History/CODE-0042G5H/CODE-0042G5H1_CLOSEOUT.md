# CODE-0042G5H1 — Entities & Authority Closeout Repair

Date: 2026-09-21
Build: Enshrouded 1076226

Status: CLOSED_OFFLINE_SOURCE_STATIC / GAMEPLAY_RUNTIME_UNPROVEN

Authoritative source:
`I:\My Drive\Enshrouded Mods\Architect_Mod\Current\runtime\ArchitectRuntime.ps1`

## Independently verified final identity

- Length: 448538 bytes
- SHA-256: `F67E9DEA0A7549966A9118385816E1AECDE4B1ACEC3799DE0E902F48E04D3A07`

Repair-start candidate:
- Length: 458779 bytes
- SHA-256: `B88E1388EDFE7CA6412C695667E1237CA7B4CA8D0EF29FC8B14844F8979A6AC0`

G5G comparison baseline:
- Length: 449290 bytes
- SHA-256: `D82ECDA9A9EAAC7837B22B640235D1C4DC63FF947A88B843D06537F1DCC0BB1B`

Registry:
- Length: 60272 bytes
- SHA-256: `7F2F5C38B75AF24B45728D5D6B6FBD5A9420BE51BF52888DD008AE77B0E21AA8`
- 55 total / 17 enabled / 38 disabled / 55 unique command IDs

## Independent source comparison

Top-level named-function comparison against archived G5G shows exactly one changed function:

- `Render-MultiplayerQuestsPage`

All other detected top-level functions are source-identical.

`Render-MultiplayerQuestsPageLegacy`:
- final definitions: 0

`Render-MultiplayerQuestsPage`:
- final definitions: exactly 1

Independent normalized function hashes:
- G5G `Render-MultiplayerQuestsPage`: `7F7A5B5C24FE62517468980B48CAFDC4888B85D4431DEA3FA335F3D5C71F5EA6`
- final `Render-MultiplayerQuestsPage`: `7DF9247BB8891D9D9610D5FA6981A3329C0549C14F110274CBCC834622096631`

Quest helper hashes are unchanged:
- `Load-QuestDatabase`: `8798C5271765F675D19E3304912B668A8D86BA1C728C191A1FC5021487C91311`
- `Load-QuestState`: `AB1F629014201EBB3A4B78BDC425AAC41F81A4C55618B7AEAB20FF65B37F9E4D`
- `Save-QuestState`: `4A6FF6DC65D44FA8CFD04253F2212FC5D3EC4A3D1564720BD9C5CFBF59A2F2AA`

## Independently source-verified repair semantics

The active responsive renderer now contains:
- state-dependent global quarantine button colors;
- selected/unselected category colors;
- Completed / In Progress / Locked / default status-color mapping;
- per-quest quarantine state colors;
- per-quest status/reset state colors;
- missing-id disabled BackColor / ForeColor plus truthful accessibility/tooltip reason;
- responsive `New-F7ResponsiveCard` / `New-F7ResponsiveTable` construction;
- local-only quest-tracker wording and UI_ONLY event routing.

The dead fixed-pixel legacy renderer has been removed.

## User/Codex-reported regression results

- Hardened G5H parity: PASS, active AST-scoped, 13 assertion groups
- Player: 18/18 PASS
- Mobility: 31/31 PASS
- Items/Progression: 46 groups PASS
- Combat: 40 groups PASS
- World/Camera: PASS
- Building: PASS
- Truthfulness: 72/72 PASS
- UI smoke: 30/30 PASS
- UI errors: 0
- Lifecycle/static: PASS
- Source consolidation/schema: 12/12 PASS
- CT catalog: 224
- Prohibited mutation scan: PASS
- H installation: absent
- Geometry: `SKIPPED_NO_WINFORMS_LAYOUT_HARNESS`

TEMP-only verification fixture:
`C:\Users\JoelT\AppData\Local\Temp\architect-code0042-g5b1r13\architect_toolkit\architect_toolkit\tests\test_g5h_entities_authority_parity.ps1`

## Evidence boundary

No quest, multiplayer, entity, gameplay, or runtime mutation mechanism was changed or proven.

H: was not recreated.
G5I was not started.
F8 was not started.

`G5H Entities & Authority responsive/parity verification is closed at source/static level.`
