# CODE-0042G1 — Batch-1 audit-foundation review

Date: 2026-09-20
Build scope: Enshrouded 1076226
Status: PARTIAL / NO RUNTIME CLAIM

## Confirmed
- `Get-F7DirectEventAudit` now exists and statically scans named renderer functions.
- `Get-F7ActionBindingAudit` exposes Batch-1 and full-F7 raw-event metrics plus event-definition counts.
- Existing 53/53 truthfulness and 28/28 UI-smoke baselines were reported green; UI errors 0.
- No responsive migration or gameplay capability was added in this slice.

## Current source measurement
Simple file-wide source counts in the current `ArchitectRuntime.ps1` are:
- `Register-SafeUiEvent`: 50 textual occurrences total (includes helper definitions/internals)
- `.Add_Click(...)`: 59 textual occurrences total
- `Register-AdminActionEvent`: 4 textual occurrences total (definition + 3 source-level uses)
- `Register-F7UiEvent`: 1 textual occurrence total (definition only)

The current Batch-1 renderer functions contain exactly 23 raw action/UI event registrations under the existing audit pattern:
- `Render-DashboardPage`: 6
- `Render-PlayerVitalsPage`: 5
- `Render-MobilityTravelPage`: 12

These 23 are the immediate G1 migration target. The F7 shell also contains direct events outside those renderer functions, including the AOB Scanner button and window/content lifecycle events; these must be deliberately classified as part of G1 shell closure.

## Architectural gaps still present
- `$script:f7EventInventory` still stores live `Control` references rather than stable metadata-only definitions.
- `Register-AdminActionEvent` and `Register-F7UiEvent` do not require a stable `EventId`.
- `Clear-AdminContent` clears visual controls but not active-binding state.
- `staleOrDisposedActiveBindings` is still hard-coded to zero.
- ambiguity checks still use `controlName`, which is not a stable unique key.
- `Register-F7UiEvent` has no real call sites yet.

## Required next move
Do not add more audit-only fields. Execute Batch-1 migration: introduce stable EventId/lifecycle semantics and convert all 23 raw events in Home/Player/Mobility plus the F7 shell events to explicit ACTION/UI_ONLY helpers. Batch-1 direct raw count must reach zero before moving to G2.
