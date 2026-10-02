# CODE-0042G1C — Home-only event migration audit

Date: 2026-09-20
Build scope: Enshrouded 1076226
Status: PARTIAL ACCEPTANCE / HOME RAW-EVENT MIGRATION COMPLETE / LIFECYCLE ACCEPTANCE NOT YET MET

## Confirmed
- `Render-DashboardPage` contains zero direct `.Add_Click(...)` registrations.
- `Render-DashboardPage` contains zero direct `Register-SafeUiEvent` registrations.
- Home now uses five `Register-AdminActionEvent` call sites plus one `Register-F7UiEvent` call site.
- Stable Home EventIds are present:
  - `f7.home.preset.apply.<presetId>`
  - `f7.home.presets.manage.click`
  - `f7.home.health.fill.click`
  - `f7.home.stamina.fill.click`
  - `f7.home.mana.fill.click`
  - `f7.home.restoreVanilla.click`
- `admin.preset.apply` exists in the registry.
- Registry contains 53 unique `commandId` entries.
- `admin.preset.apply` is disabled / `ORCHESTRATION_ONLY`; it does not add a new mutation backend.
- Existing safety restrictions remain fail-closed.

## Important remaining issue
The Home raw-registration migration is complete, but the lifecycle part of the G1C acceptance contract is not yet complete.

Current helper behavior still:
- stores strong WinForms `Control` references in `$script:f7EventInventory`;
- appends a new inventory record every time the same EventId is re-rendered;
- stores active controls in `$script:adminActionControls`;
- does not clear/replace active binding state in `Clear-AdminContent`;
- computes `duplicateEventIds` from the accumulating inventory;
- hard-codes `staleOrDisposedActiveBindings=0`.

Therefore rendering Home twice can create duplicate EventId definitions and stale/disposed control references even though `Render-DashboardPage` itself has no raw events.

## Acceptance status
PROVEN source-level:
- Home raw direct-event count = 0.
- Home controls have explicit ACTION/UI_ONLY registration paths.

NOT YET PROVEN / structurally not satisfied:
- Home definition count stable across rerender.
- duplicate Home EventIds = 0 after rerender.
- stale/disposed Home active bindings = 0 after rerender.
- metadata-only stable denominator independent of WinForms object lifetime.

## Recommended next bounded pass
Before migrating Player Vitals, repair the shared event lifecycle helpers:
1. Stable definition inventory keyed by EventId, metadata only.
2. Separate active binding map keyed by EventId.
3. Re-registering an EventId replaces/refreshes active state instead of appending definition duplicates.
4. `Clear-AdminContent` / page transition clears active bindings for the outgoing render generation/page.
5. `staleOrDisposedActiveBindings` is measured, not hard-coded.
6. Existing Home events still render and bind correctly.
7. No gameplay, registry-enable, responsive-layout, or safety behavior changes.
