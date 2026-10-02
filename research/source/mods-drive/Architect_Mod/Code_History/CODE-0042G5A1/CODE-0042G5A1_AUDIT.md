# CODE-0042G5A1 — Home responsive cleanup audit

Date: 2026-09-21
Build scope: Enshrouded 1076226
ArchitectRuntime.ps1 SHA-256: 92434e1883797b83ba33dabdabdaecb7fce198f2461e20d08498a647f7362632
admin_action_registry.json SHA-256: 7f2f5c38b75af24b45728d5d6b6fbd5a9420be51bf52888dd008ae77b0e21aa8
Registry actions: 55
Enabled: 17
Disabled: 38

Status: SOURCE-VERIFIED G5A1 CLEANUP / GEOMETRY HARNESS SKIPPED / NO GAMEPLAY CLAIM

## Source-verified G5A1

The current runtime no longer contains `Render-DashboardPage.LegacyFixed`.

Exactly one active `Render-DashboardPage` remains.

The old dynamic fixed-position preset formula is gone from Home:

`$bx = 10 + ...`

`Render-DashboardPage` no longer uses `[scriptblock]::Create`.

The three pre-G5A instant-action handlers/status strings are restored exactly:

- `f7.home.health.fill.click` -> `player.health.fill`
  - `Player health restored to 100%.`
- `f7.home.stamina.fill.click` -> `player.stamina.fill`
  - `Player stamina restored to 100%.`
- `f7.home.mana.fill.click` -> `player.mana.fill`
  - `Player mana restored to 100%.`

Telemetry cell placement is now explicit:

- Engine -> column 0, row 0
- Coordinates -> column 0, row 1
- Local Quest Flag -> column 1, row 0
- Watchdog -> column 1, row 1

The responsive Home structure introduced in G5A remains in place.

Registry remains unchanged at 55 / 17 enabled / 38 disabled.

## Test provenance

Reported by user/Codex:

- PowerShell parse: PASS
- lifecycle/static fixture: PASS
- F7 truthfulness: 53/53 PASS
- UI smoke: 28/28 PASS
- UI errors: 0
- CT catalog: 224
- corrected G4A zero-gap static audit: PASS
- no legacy Home function/reference remains
- registry unchanged: 55 / 17 / 38

Responsive geometry validation remains:

`SKIPPED_NO_WINFORMS_LAYOUT_HARNESS`

No runtime geometry, horizontal-scroll behavior, gameplay behavior, or native mechanism is established.

## Next responsive slice

The next renderer is intentionally bounded to Player only.

`Render-PlayerVitalsPage` is substantially denser than Home:
- header actions
- vitals/recovery card
- 12-row survival override surface
- primary attributes row
- weapon-scaling row

Mobility remains a separate follow-on slice so layout regressions can be isolated.
