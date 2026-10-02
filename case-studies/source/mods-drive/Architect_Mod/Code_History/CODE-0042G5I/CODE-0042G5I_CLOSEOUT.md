# CODE-0042G5I — Mods & Configuration Responsive Closeout

Date: 2026-09-21
Build: Enshrouded 1076226

Status: CLOSED_OFFLINE_SOURCE_STATIC / GAMEPLAY_RUNTIME_UNPROVEN

Authoritative source:
`I:\My Drive\Enshrouded Mods\Architect_Mod\Current\runtime\ArchitectRuntime.ps1`

## Independently verified final identity

- Length: 448462 bytes
- SHA-256: `2CFD1FA80A0B8FF6647E0816489AD3534D78F43F264D75B9330A857DECE0751C`

Starting G5H baseline:
- Length: 448538 bytes
- SHA-256: `F67E9DEA0A7549966A9118385816E1AECDE4B1ACEC3799DE0E902F48E04D3A07`

Registry:
- Length: 60272 bytes
- SHA-256: `7F2F5C38B75AF24B45728D5D6B6FBD5A9420BE51BF52888DD008AE77B0E21AA8`
- 55 total / 17 enabled / 38 disabled / 55 unique command IDs

## Independent function-diff verification

Top-level named-function comparison between archived G5H and final Current shows exactly one changed function:

- `Render-SettingsDevPage`

Function hash:
- before: `678348E5FD08C34A461211B3C28EC7EA57B20C4A22CA47C6DD94D89D848A1654`
- after: `59FE4E3EF9BD537C622B9F92C1F7E47BFA27B2A3E164505C33A6F54022BC255F`

All other detected top-level functions are source-identical under the same extraction method.

Exactly one active `Render-SettingsDevPage` remains.
No `Render-SettingsDevPageLegacy` or backup renderer was introduced.

The reported Dashboard mismatch was a regex extraction artifact; function-scope comparison confirms the protected Dashboard renderer is unchanged.

## Independently source-verified G5I semantics

The active renderer uses `New-F7ResponsiveCard` and `New-F7ResponsiveTable`.

Preserved source semantics include:
- `HOTKEYS` selected subview with no handler;
- UI_ONLY Role Presets navigation:
  `f7.settings.subnav.presets.click`;
- UI_ONLY Native Diagnostics navigation:
  `f7.settings.subnav.diagnostics.click`;
- canonical Panic Reset:
  `f7.settings.panicReset.click` -> `cheat.survival.disable_all`;
- panic handler reports success only after a successful dispatch;
- seven hotkey binding definitions preserved;
- key choices from `virtualKeyMap`;
- save-through-`Get-CodeFromKeyName` / `Save-ArchitectKeybindings`;
- HUD close-hint refresh preserved;
- immersion preference keys:
  `theatric_auto_summon_wand`
  and `auto_dock_on_holster`;
- preference apply remains UI_ONLY and persisted through `Save-ArchitectKeybindings`.

Canonical Panic Reset remains fail-closed in the registry:
- enabled = false
- evidenceStatus = UNSOLVED
- backend = NONE
- runtimeMode = UNAVAILABLE
- authority = unknown
- risk = mutation

No Role Presets or Diagnostics renderer change is accepted as part of G5I.

## User/Codex-reported regression results

- G5I parity fixture: PASS
- Player: 18/18 PASS
- Mobility: 31/31 PASS
- Items/Progression: 46 groups PASS
- Combat: 40 groups PASS
- World/Camera: PASS
- Building: PASS
- Entities/Authority: PASS
- Truthfulness: 72/72 PASS
- UI smoke: 30/30 PASS
- UI errors: 0
- Lifecycle/static: PASS
- Source consolidation/schema: 12/12 PASS
- CT catalog: 224
- Prohibited mutation scan: PASS
- Registry: 55 / 17 / 38 / 55 unique
- H installation: absent
- Geometry: `SKIPPED_NO_WINFORMS_LAYOUT_HARNESS`

## Evidence boundary

G5I is closed at source/static level only.

No gameplay/runtime mechanism was changed or proven.
Role Presets and Diagnostics were not modified.
H: was not recreated.
G5J was not started.
F8 was not started.

`G5I Mods & Configuration responsive/parity verification is closed at source/static level.`
