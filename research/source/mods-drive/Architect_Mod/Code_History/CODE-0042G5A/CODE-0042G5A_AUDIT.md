# CODE-0042G5A — Responsive Foundation + Home audit

Date: 2026-09-21
Build scope: Enshrouded 1076226
ArchitectRuntime.ps1 SHA-256: 1ed01100afbad5f0f6552adb618071fc6af100f457626e6af98aaba3ba7cf798
admin_action_registry.json SHA-256: 7f2f5c38b75af24b45728d5d6b6fbd5a9420be51bf52888dd008ae77b0e21aa8
Registry actions: 55
Enabled: 17
Disabled: 38

Status: RESPONSIVE STRUCTURE SOURCE-VERIFIED / THREE BOUNDED SOURCE DEVIATIONS / GEOMETRY HARNESS SKIPPED / NO GAMEPLAY CLAIM

## Source-verified G5A structure

Current source contains:

- `New-F7ResponsiveCard`
- `New-F7ResponsiveTable`
- `Resize-AdminPageChildren` calling child `PerformLayout()` and then `$adminContent.PerformLayout()`

The executable `Render-DashboardPage` now uses responsive containers for:

- header
- telemetry
- quick role presets
- instant actions
- hotkey summary
- restore-vanilla control

Existing Home ActionIds/EventIds are still represented.

The G4A semantic boundary is unchanged and the user/Codex-reported corrected zero-gap fixture remains PASS.

## Geometry proof status

The WinForms responsive geometry harness was unavailable.

Therefore:
`SKIPPED_NO_WINFORMS_LAYOUT_HARNESS`

No runtime claim is made about:
- clipping
- minimum-size layout
- horizontal scroll
- actual resize behavior

## Three bounded source deviations

### 1. Legacy fixed Home implementation was retained in runtime source

Current runtime adds a `Render-DashboardPage.LegacyFixed` function containing the old Home implementation inside a block comment.

The body is not executable, but this duplicates stale UI/event source text inside the production runtime.

Problems:
- makes future source searches/diffs noisier;
- preserves stale fixed-layout/event text in Current;
- can confuse simplistic static tests or human audits;
- is unnecessary because Code_History already preserves prior source.

Recommended repair:
remove the entire `Render-DashboardPage.LegacyFixed` function.

### 2. Instant-action handler semantics drifted in a layout-only pass

Pre-G5A handlers were explicit:

- `player.health.fill` -> status `Player health restored to 100%.`
- `player.stamina.fill` -> status `Player stamina restored to 100%.`
- `player.mana.fill` -> status `Player mana restored to 100%.`

G5A replaces these with a generated scriptblock using `[scriptblock]::Create(...)` and generic `<operation> completed.` status text.

This preserves ActionIds/EventIds but changes handler/status semantics and introduces runtime-generated handler source.

Because G5A was scoped as layout-only, restore the exact pre-G5A handlers rather than changing command semantics during responsiveness work.

Do not attempt a broader truthfulness redesign in this repair; preserve the pre-G5A behavior exactly.

### 3. Telemetry 2x2 cell mapping is not the requested mapping

Current array/add loop places:

- Engine -> column 0 row 0
- Coordinates -> column 1 row 0
- Local Quest Flag -> column 0 row 1
- Watchdog -> column 1 row 1

Intended mapping was:

- left/top: Engine
- left/bottom: Coordinates
- right/top: Local Quest Flag
- right/bottom: Watchdog

This should be made explicit with direct `Controls.Add(control, column, row)` calls instead of index arithmetic.

## Test provenance

Reported by user/Codex:

- PowerShell parse: PASS
- lifecycle/static fixture: PASS
- F7 truthfulness: 53/53 PASS
- UI smoke: 28/28 PASS
- UI errors: 0
- CT catalog: 224
- G4A zero-gap fixture: PASS
- registry unchanged: 55 / 17 / 38
- geometry harness: SKIPPED_NO_WINFORMS_LAYOUT_HARNESS

No gameplay/runtime behavior is established.
