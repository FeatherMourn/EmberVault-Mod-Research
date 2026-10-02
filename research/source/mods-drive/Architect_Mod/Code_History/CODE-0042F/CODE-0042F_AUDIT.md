# CODE-0042F — Raw-event closure audit

Date: 2026-09-20
Game build scope: Enshrouded 1076226
Baseline: Architect Toolkit 0.42.0 / INC-0062
Status: SOURCE-AUDITED / PARTIAL CODE-0042F / NO RUNTIME CLAIM

## Confirmed
- `directUnclassifiedEventRegistrations` is now present on `Get-F7ActionBindingAudit`.
- PowerShell source remains parseable per the Codex report.
- Existing safety restrictions were not intentionally changed in this slice.
- Registry remains at 52 actions from CODE-0042E unless independently changed elsewhere.

## Critical issue — the new metric still cannot detect raw event registrations
The current implementation computes:

`directUnclassifiedEventRegistrations = @($script:f7EventInventory | ? {-not $_.Classification}).Count`

This only counts records that are already inside the inventory but lack a classification. Raw `Register-SafeUiEvent` and `.Add_Click(...)` sites bypass the inventory entirely, so they cannot contribute to this metric. Therefore this field may report zero while many direct unclassified registrations still exist.

Required repair: compute the direct-unclassified count from an independent source/event-surface scan, or eliminate every raw event registration in the defined F7 surface and verify that fact statically.

## Current raw-registration volume
Static inspection of the current source finds:
- 48 direct `Register-SafeUiEvent` calls;
- 58 `.Add_Click(...)` registrations;
- 106 total call sites file-wide.

Two `Register-SafeUiEvent` calls are the intended internals of `Register-AdminActionEvent` and `Register-F7UiEvent`. Approximately eight additional raw event registrations are F8-specific and outside the F7 audit surface. The defined F7 renderer/shell surface therefore contains approximately 96 raw direct event registrations that still need classification/migration.

High-volume F7 areas include:
- `Render-MobilityTravelPage`: 12
- `Render-CombatAIPage`: 12
- `Render-WorldCameraPage`: 9
- `Render-MapWayfinderPage`: 9
- `Render-InventoryItemsPage`: 7
- `Show-BlueprintBrowser`: 7
- `Render-DashboardPage`: 6
- `Render-PlayerVitalsPage`: 5
- `Render-SettingsDevPage`: 5
- `Render-CodexWikiPage`: 5
- `Render-MultiplayerQuestsPage`: 4
- `Update-CodexDetails`: 4
- `Render-CraftingProgressionPage`: 3
- `Render-BuildingEntitiesPage`: 3
- `Render-RolePresetsPage`: 2
- `Update-WaypointDetails`: 1
- `Show-AdminPage` / F7 shell-related registrations: additional UI events

This count is a migration target, not proof that all 96 are ACTION controls. Each must be explicitly classified as ACTION or UI_ONLY.

## Lifecycle issue remains unresolved
`$script:f7EventInventory` still stores strong `Control` references, and `$script:adminActionControls` stores live controls in per-ActionId ArrayLists. `Clear-AdminContent` still only calls `$adminContent.Controls.Clear()`.

Repeated page renders can therefore retain disposed/stale controls and make counts dependent on navigation history. The event inventory needs stable metadata identity independent of WinForms object lifetime, and active control references need deterministic cleanup.

## Stable identity issue remains unresolved
Inventory entries still use `ControlName`/display text without a mandatory stable EventId/ControlKey. Dynamic WinForms controls frequently have empty or reused names. Ambiguity checks must use an explicit stable ID supplied by the renderer/helper, not `Control.Name` alone.

## Recommended closure architecture
Use two layers:

1. Stable event-definition inventory (metadata only, keyed by mandatory `EventId`)
   - EventId
   - Page
   - Classification: ACTION or UI_ONLY
   - ActionId for ACTION
   - EventName
   - Operation
   - source/renderer context if useful
   - no strong Control reference

2. Active-render binding map
   - EventId -> current Control reference / render generation
   - cleared or replaced deterministically when a page is re-rendered
   - never used as the denominator for full-project coverage

`Register-AdminActionEvent` and `Register-F7UiEvent` should both require EventId and populate the stable definition inventory. The ACTION helper then performs canonical ActionId binding. Re-rendering the same EventId replaces/refreshes active state instead of appending duplicates.

## Direct-unclassified proof
The strongest acceptance check is static:
- define the F7 audit surface explicitly (F7 shell, all 11 page renderers, F7 subviews/dialogs/codex/wayfinder/blueprint UI);
- exclude F8-only functions;
- permit raw `Register-SafeUiEvent` only inside the two registration helpers;
- permit no direct `.Add_Click(...)` inside the F7 audit surface;
- report the remaining count as `directUnclassifiedEventRegistrations`.

## Acceptance gate before responsive migration
Do not proceed to broad responsive page migration until all are true:
- `unboundActionControls = 0`
- `missingRegistryIds = 0`
- `ambiguousBindings = 0`
- `directUnclassifiedEventRegistrations = 0`
- no duplicate stable EventIds
- repeated traversal of all 11 pages yields identical definition counts regardless of order/repetition
- no disposed/stale control references remain in active bindings after page transitions
- 224-entry CT catalog remains preserved
- 53/53 truthfulness and 28/28 UI smoke remain green or are strengthened without weakening assertions
- prohibited direct F7 mutation fallbacks remain absent

Compilation/parse success does not establish runtime proof.
