# CODE-0042G1C2 — Lifecycle-foundation source audit

Date: 2026-09-20
Build scope: Enshrouded 1076226
Current ArchitectRuntime.ps1 SHA-256: a43fc9ec4ff7e9e441ab9f42aa1dca5af096028ee72f895bbf6a133956214a5d
Current admin_action_registry.json SHA-256: e4be1f20c0014bcebb671c9b2a2f1e751c259ff4f308637a63a82079262f5e5c
Registry action count: 53
Status: SOURCE-AUDITED / PARTIAL LIFECYCLE FOUNDATION / NO RUNTIME CLAIM

## Confirmed
- `$script:f7EventDefinitions` exists and is keyed by EventId.
- `$script:f7ActiveBindings` exists separately from stable definitions.
- `Clear-AdminContent` resets `$script:f7ActiveBindings` and `$script:adminActionControls` before clearing WinForms children.
- `Get-F7ActionBindingAudit` derives event-definition rows from `$script:f7EventDefinitions`.
- `staleOrDisposedActiveBindings` is now computed from current active-binding controls using `IsDisposed`; it is no longer hard-coded.
- Home retains stable EventIds and `Render-DashboardPage` still has zero direct `.Add_Click(...)` and zero direct `Register-SafeUiEvent` registrations.
- Registry remains 53 actions and `admin.preset.apply` remains disabled / orchestration-only.

## Blocking lifecycle defect: legacy strong-reference inventory still remains
The old `$script:f7EventInventory = New-Object System.Collections.ArrayList` still exists.

Both registration helpers still append records containing the live WinForms `Control`:
- `Register-AdminActionEvent` appends an ACTION record with `Control=$Control`.
- `Register-F7UiEvent` appends a UI_ONLY record with `Control=$Control`.

`Clear-AdminContent` does not clear `$script:f7EventInventory`.

Therefore repeated page renders can still retain old controls through this legacy collection even though the new audit denominator uses `$script:f7EventDefinitions`. The new definition/binding split is present, but the implementation is not yet fully lifecycle-safe.

The legacy inventory appears to be write-only in current source and should be removed or converted to metadata-only data if a compatibility consumer actually requires it.

## Binding helper coupling
`Bind-AdminActionControl` calls `Register-F7EventDefinition` and writes an EventId tag, but its parameter list contains only Control, ActionId, Page, and AllowDisabled. It relies on `EventId`, `EventName`, and `Operation` being visible from the calling `Register-AdminActionEvent` scope.

Current source has only one call site for `Bind-AdminActionControl`, so this works only through caller-scope coupling. It should be made explicit: either pass EventId/EventName/Operation into the helper, or move definition registration/tagging into `Register-AdminActionEvent` and keep `Bind-AdminActionControl` focused on capability/accessibility binding.

## Ambiguity comparison should be made explicit
`Register-F7EventDefinition` currently compares grouped property lists with one `-ne` expression. Before repeated-render stability is accepted, replace this with explicit field-by-field comparison of Page, Classification, ActionId, EventName, and Operation. This avoids array/comparison semantics influencing ambiguity detection.

## Acceptance status
SOURCE-VERIFIED:
- stable-definition map exists;
- active-binding map exists;
- active/action maps clear on `Clear-AdminContent`;
- active stale count is computed;
- Home raw event count remains zero.

NOT YET ACCEPTED:
- no historical strong Control references after rerenders;
- duplicate/ambiguity behavior under repeated Home traversal;
- stable Home definition count under repeated traversal;
- exact current active bindings after page transitions.

## Required next pass
Do not migrate Player or Mobility yet.

1. Remove the legacy strong-reference `$script:f7EventInventory` path (or make it metadata-only if proven necessary).
2. Remove caller-scope dependency from `Bind-AdminActionControl`.
3. Make EventId conflict comparison explicit field-by-field.
4. Add a repeated Home traversal test:
   - Home render
   - another page / clear
   - Home render
   - Home rerender
5. Assert:
   - stable Home definition count;
   - duplicate Home EventIds = 0;
   - ambiguous Home bindings = 0;
   - stale/disposed active bindings = 0;
   - no historical controls retained by any event inventory;
   - active bindings correspond only to the current render;
   - Home raw direct events remain 0.
6. Preserve all existing safety, registry, catalog, truthfulness, and UI-smoke baselines.

Only after this passes should Player Vitals event migration begin.
