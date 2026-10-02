# CODE-0042G1C3 — Lifecycle repair source audit

Date: 2026-09-20
Build scope: Enshrouded 1076226
Current ArchitectRuntime.ps1 SHA-256: 00217521b764431e2c5033740386f3f6237809376f6c7a9a533c9d1834a9dad4
Registry action count: 53
Status: SOURCE-AUDITED / PARTIAL ACCEPTANCE / NO RUNTIME CLAIM

## Confirmed
- The legacy `$script:f7EventInventory` strong-reference collection is gone from current source.
- Stable definitions exist in `$script:f7EventDefinitions`.
- Live controls exist separately in `$script:f7ActiveBindings`.
- `Clear-AdminContent` clears `$script:f7ActiveBindings` and `$script:adminActionControls` before clearing page controls.
- `Register-F7EventDefinition` now performs explicit field-by-field conflict comparison for Page, Classification, ActionId, EventName, and Operation.
- `Get-F7ActionBindingAudit` computes stale/disposed active bindings from current active controls using `IsDisposed`.
- `Render-DashboardPage` still contains zero direct `.Add_Click(...)` registrations and zero direct `Register-SafeUiEvent` calls.
- Home still uses five `Register-AdminActionEvent` registrations and one `Register-F7UiEvent` registration.
- Registry remains 53 unique action IDs.
- Prohibited direct NativeMemoryEngine mutation calls remain absent for TogglePatch, EnableAllSurvival, DisableAllSurvival, WritePlayerCoordinates, ToggleAutoLoot, and ToggleGliderFlight.

## Remaining source defect — caller-scope dependency still exists
The current source does not satisfy the reported claim that `Bind-AdminActionControl` no longer depends on caller scope.

`Bind-AdminActionControl` accepts only:
- Control
- ActionId
- Page
- AllowDisabled

But inside the function it still references:
- `$EventId`
- `$EventName`
- `$Operation`

Those values are supplied only because `Bind-AdminActionControl` is invoked from `Register-AdminActionEvent`, whose local scope contains variables with those names.

`Register-AdminActionEvent` currently calls:

`Bind-AdminActionControl -Control $Control -ActionId $ActionId -Page $Page`

without passing EventId/EventName/Operation.

This is PowerShell dynamic-scope coupling. It may function today, but it violates the explicit lifecycle architecture and makes direct/helper-level testing brittle.

Required repair:
- either pass EventId/EventName/Operation explicitly into `Bind-AdminActionControl`; or
- preferably register the stable event definition in `Register-AdminActionEvent`, then pass EventId explicitly to a narrower binding helper that only performs canonical action/control binding and active-binding registration.

## Remaining verification gap
The dedicated repeated-Home traversal/lifecycle test is still absent.

The source architecture is now close enough for that test after the caller-scope dependency is removed.

The test should verify repeated Home render/navigation produces:
- identical stable Home EventId set;
- stable definition count;
- zero duplicate/ambiguous EventIds;
- zero missing Home registry IDs;
- zero stale/disposed active bindings;
- only current-render live controls in active bindings;
- zero Home raw direct events.

## Acceptance
SOURCE-VERIFIED:
- legacy strong-reference inventory removed;
- stable definition/live binding split exists;
- Home raw event migration remains complete;
- registry/safety state preserved.

NOT YET ACCEPTED:
- no caller-scope dependency in action binding;
- repeated Home lifecycle stability under automated traversal.

Do not begin Player Vitals migration until these two items are green.
