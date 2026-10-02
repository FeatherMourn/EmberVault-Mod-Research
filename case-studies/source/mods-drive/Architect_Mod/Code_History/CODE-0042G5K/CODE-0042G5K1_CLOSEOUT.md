# CODE-0042G5K1 — Role Presets Closeout Repair

Date: 2026-09-21
Build: Enshrouded 1076226

Status: CLOSED_OFFLINE_SOURCE_STATIC / GAMEPLAY_RUNTIME_UNPROVEN

Authoritative source:
`I:\My Drive\Enshrouded Mods\Architect_Mod\Current\runtime\ArchitectRuntime.ps1`

## Independently verified final identity

- Length: 449783 bytes
- SHA-256: `9EF34615CD233BFBA2AFB885C7EA84D71343E019F4FA1647B93C004AC42585E9`

Repair-start candidate:
- Length: 449765 bytes
- SHA-256: `0CCE15A6FC9C8DF2DDA6B40CE86809A1A72B5F5B962D905651C2981477EF5E48`

Archived G5J baseline:
- Length: 449835 bytes
- SHA-256: `D510D65A3A25FB4080DC3BC466AD9D0736661FF0E2F3F291989721437F366EF8`

Registry:
- Length: 60272 bytes
- SHA-256: `7F2F5C38B75AF24B45728D5D6B6FBD5A9420BE51BF52888DD008AE77B0E21AA8`
- 55 total / 17 enabled / 38 disabled / 55 unique command IDs

## Independent source verification

Top-level named-function comparison against archived G5J shows exactly one changed function:

- `Render-RolePresetsPage`
  - G5J: `4F85385E794C0C487840103DEE28B390A9A3A273F093F6B1EDDF2069E55449E2`
  - final: `A808FC02490B42F66BBCE7A493C3E113CD2F51693EEAD2F146DB38A2F3A23647`

Preset helpers are source-identical:
- `Load-ArchitectPresets`: `98E731A7608EC050106E5F64A9F63162BAEBB081041D170563D1EFF87063397C`
- `Save-ArchitectPresets`: `84A378F49AB5B9B3ADA30E4DE3A93EBD5952E14AC42918FA0048D35A0F656A28`
- `Invoke-ArchitectPreset`: `95F1FE81057B5ADFE3C1B3C4EB7D41679E0628000B60D81F71C26C26108F003D`

Exactly one active `Render-RolePresetsPage` exists.
No Legacy/Old/Backup/Copy Role Presets function exists.

Candidate-to-final diff is exactly the WORLD EXPLORER fallback description repair:

`Shroud Immunity, Underwater Breathing, Cold Immunity, Infinite Stamina, 2.5x Movement Speed.`

No other source line changed between the blocked candidate and repaired final.

## Canonical preset safety boundary

`admin.preset.apply` remains:
- enabled = false
- evidenceStatus = EXPERIMENTAL
- backend = NONE
- runtimeMode = SESSION
- authority = unknown
- risk = compound_mutation
- failureReason = `Preset execution must fail closed when any child action is unavailable.`

No preset helper, persistence, navigation, registry, native, gameplay, or runtime mechanism changed.

## User/Codex-reported regression results

- G5K parity: PASS
- G5B-G5J regression fixtures: PASS
- Lifecycle/static: PASS
- Truthfulness: 72/72 PASS
- UI smoke: 30/30 PASS
- UI errors: 0
- Registry: PASS
- CT catalog: 224
- H installation: absent
- Geometry: `SKIPPED_NO_WINFORMS_LAYOUT_HARNESS`

The hardened G5K fixture now asserts all four fallback descriptions exactly within the active Role Presets function scope.

## Evidence boundary

G5K is closed at source/static level only.

Preset execution and gameplay behavior remain unproven and fail closed.
H: was not recreated.
F8/later work was not started.

`G5K Role Presets responsive/parity verification is closed at source/static level.`
