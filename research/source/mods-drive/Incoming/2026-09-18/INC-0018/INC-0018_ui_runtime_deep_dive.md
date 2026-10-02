# INC-0018 — Architect Toolkit UI / Runtime Deep Dive

Date: 2026-09-18
Game build: 1076226
Uploaded archive SHA-256: `7709b88ab2c6aa50e08a162eccc3a13cda05cb7617656207e4dfdbaa11fb091b`
Native DLL SHA-256: `85f6e1c7ba9bebcc74df8358329d301a62a98cb27a36ef351d4de9e8c3e3e257`
ArchitectRuntime.ps1 SHA-256: `12c7be17210ddd4e78ede1fd68162905691db11b5cfdf96c61f3d302685534a7`

## Executive summary

The current package is no longer dominated by one native crash. The largest reliability problem is now the PowerShell/WinForms UI architecture: a ~5,600-line monolithic runtime with 136 event registrations, fixed-position controls, optimistic command status, event callbacks that can outlive local variables, and many swallowed exceptions. The screenshot's modal PowerShell error is traceable to Inventory page event handlers that invoke a local scriptblock with the call operator after the page-render function has returned.

The F7 window is intentionally non-resizable (`FormBorderStyle=None`) and its entire shell uses fixed pixel coordinates/sizes. The 25 ms timer also re-centers the admin form continuously while visible, which would fight user movement/resizing even if the border style were changed.

Native fail-closed behavior is improved, but current status still shows the hook framework inactive after `HOOK_INSTALL_FAILED_SKILLS`, while several F7 controls remain enabled and continue to queue commands that the native log rejects. This creates a noisy and confusing UI even when native safety is functioning correctly.

## PROVEN findings

### 1. Screenshot exception path: local filter callback invoked after render scope

`Render-InventoryItemsPage` defines a local `$populateSpawnList = { ... }`, invokes it once, then registers delayed handlers:

- `ArchitectRuntime.ps1:2618` local scriptblock definition
- `ArchitectRuntime.ps1:2636` initial `& $populateSpawnList`
- `ArchitectRuntime.ps1:2637` `SelectedIndexChanged({ & $populateSpawnList })`
- `ArchitectRuntime.ps1:2638` `TextChanged({ & $populateSpawnList })`

The screenshot's exact PowerShell exception is: `The expression after '&' in a pipeline element produced an object that was not valid...`. On the Inventory page, these are the only matching delayed call-operator paths. The same defect pattern exists in Mobility/Travel:

- `ArchitectRuntime.ps1:2433` `$populateList = { ... }`
- `ArchitectRuntime.ps1:2451-2452` delayed `{ & $populateList }`

These callbacks need durable closures or, preferably, named/controller-backed handlers instead of referencing ephemeral local scriptblock variables.

### 2. No UI exception boundary

There are 136 `.Add_*` event registrations in `ArchitectRuntime.ps1`. Most execute directly without a common try/catch/logger. The file's outer `try/catch` does not prevent modal WinForms event-handler exception dialogs. The timer also contains many empty `catch {}` blocks, so some failures disappear while others produce modal crashes.

Required fix: one central `New-SafeUiHandler`/`Register-SafeUiEvent` wrapper plus `ui_errors.log` with page/control/event/action/stack trace. No normal UI exception should surface as a Windows unhandled-exception dialog.

### 3. F7 is explicitly fixed-size / frameless

- `ArchitectRuntime.ps1:1906` `FormBorderStyle=None`
- `ArchitectRuntime.ps1:1908` fixed `900x590`
- header/nav/body/content/status all use fixed pixel coordinates
- content panel fixed at `624x388`

This is why it cannot resize.

### 4. Continuous re-centering will fight resizable/movable behavior

The 25 ms timer calls `Position-AdminWindow` whenever F7 is visible (`ArchitectRuntime.ps1:5566-5568`). A resizable/movable window should be positioned on first show only, not forcibly re-centered ~40 times/sec.

### 5. Hook framework is currently inactive, but hook-dependent controls remain interactable

Bundled `cheat_correlation_status.json` says:

- `active=false`
- `hooksInstalled=0`
- all hook readiness flags false
- `lastFailure=HOOK_INSTALL_FAILED_SKILLS`

Bundled `native_runtime.log` shows repeated fail-closed rejections for health fill, stamina fill, mana fill, jump, god mode, mana/stamina toggles, and time set.

However current F7 still leaves several controls enabled and immediately prints optimistic text:

- Health/Stamina/Mana Fill buttons remain enabled and say `refill queued`.
- Movement speed and jump multiplier buttons remain enabled.
- Skill-points controls remain enabled despite `skillsHookReady=false`.
- Time controls remain enabled despite `daytimeHookReady=false`.
- Survival badge controls can remain clickable even when their capability is false.

UI readiness must disable the control itself, not merely paint the badge OFF.

### 6. Inventory Reroll is enabled while pointer is zero

The screenshot shows `Active Item Pointer Hook: 0x0`, but `REROLL ACTIVE ITEM PERKS` is enabled. `Render-InventoryItemsPage` does not capability-gate the button. It should require both a proven inventory-capture capability and a nonzero validated active-item pointer before enabling.

### 7. Command flow still reports intent before authoritative result

`Send-CheatCommand()` publishes `queued` and many click handlers immediately call `Set-AdminStatus` with success-sounding text. Native later rejects the command. This means the UI can say `set`, `paused`, `restored`, etc. before an ACK/readback exists.

Required state machine: `DISABLED -> READY -> PENDING -> APPLIED_UNVERIFIED -> VERIFIED`, with `REJECTED/FAILED` terminal paths. Only VERIFIED may display ON/success.

### 8. Legacy C# mutation fallback remains mixed into command publication

`Send-CheatCommand()` still attempts `NativeMemoryEngine` operations when native cheat status is not active, then also publishes a native command. This is legacy dual-path complexity even though prior architecture designated native runtime as mutation owner. Remove mutation side effects from UI routing; one action should have one owner.

### 9. Direct-patch UI capability checks are too broad

`Get-CheatCapabilityReady()` treats direct-patch features as ready when only `status.build.supported` is true. It does not consume per-patch target readiness/expected-byte/readback capability. Expose explicit per-feature readiness booleans and gate UI on them.

### 10. Diagnostics disagree about mutation state

`native_status.json` hardcodes `mode=observe_only_cheat_correlation`, `targetGameMutation=false`, and `targetGameMutationScope=none_observe_only`, while `cheat_correlation_status.json` reports direct patch states such as `altarArea=true`, `altarFar=true`, `buildRange=true`, `plantGrowth=true`, and `gliderStamina=true`. One authoritative status model is needed.

### 11. Fake current-position fallback remains

`Get-CurrentPlayerPosition()` returns hard-coded `{X=2410,Y=150,Z=-1205}` if no real position source succeeds. The UI can therefore display a fabricated location. Return `UNAVAILABLE`/`$null` instead.

### 12. Packaging recursively embeds a previous test ZIP

The uploaded archive is ~75 MB because it contains `Export/Test_Builds/architect_toolkit.zip` (~38 MB) inside the source tree. The inner ZIP has SHA `752ebbf...6a93`. Packaging should exclude `Export/Test_Builds/*.zip`, build artifacts, object files, `__pycache__`, and prior packages from the distributable unless explicitly requested.

## UI redesign recommendation

For F7, reliability is more important than maintaining a frameless custom window.

Use a normal resizable form initially:

- `FormBorderStyle = Sizable`
- `MinimumSize = 900x590`
- `Size = 1000x700` default
- `MaximizeBox = true`
- `SizeGripStyle = Show`

Refactor shell layout:

- Header: `Dock=Top`, fixed height 74
- Main area: `SplitContainer` or `TableLayoutPanel`, `Dock=Fill`
- Navigation: left pane, fixed/min width ~180
- Body: `Dock=Fill`
- Page title: `Dock=Top`
- Status: `Dock=Bottom`
- Content host: `Dock=Fill`, `AutoScroll=true`

Keep a minimum size so existing fixed-width cards remain usable during first pass. Then progressively replace page absolute-position cards with vertical `FlowLayoutPanel`/`TableLayoutPanel` roots.

Position admin window only on first show or when no saved bounds exist. Persist last bounds in preferences and never re-center it each timer tick.

## Recommended implementation sequence

### Phase 0 — Freeze native feature expansion
Do not add more cheats while UI/runtime error handling is unstable. Preserve current native fail-closed behavior.

### Phase 1 — Crash containment
1. Add safe UI event wrapper and structured `ui_errors.log`.
2. Fix Inventory and Mobility local callback lifetime defects.
3. Audit all 136 events for delayed references to page-local scriptblocks/controls.
4. Replace empty catches in critical UI/bridge paths with bounded logging.
5. Add a UI smoke harness that programmatically opens every page and triggers non-mutating controls/filter events.

### Phase 2 — Truthful UI state
1. Build one capability model consumed by every page.
2. Disable controls when dependency is unavailable.
3. Inventory reroll requires nonzero validated item pointer.
4. Remove optimistic Set-AdminStatus messages before ACK.
5. Track pending commands by commandId and resolve them asynchronously from native status/ACK.
6. Remove legacy C# mutation fallback from UI command routing.

### Phase 3 — Resizable F7 shell
1. Switch to `Sizable` form with minimum size.
2. Dock shell panels.
3. Stop 25 ms recentering.
4. Persist/restore window bounds.
5. Add resize tests for 900x590, 1280x720, 1600x900, maximized.

### Phase 4 — Page modularization
Split the monolithic PowerShell runtime into modules:

- `UiShell.psm1`
- `UiEventSafety.psm1`
- `AdminCapabilityModel.psm1`
- `AdminCommandClient.psm1`
- one page module per F7 category
- F8 builder module separate from F7

Page modules should receive a context object instead of using many global/script variables.

### Phase 5 — Native capability work
Only after UI stabilization, continue the feature-scoped native hook work. Current first native failure remains Skills hook installation; do not weaken rollback semantics.

## Acceptance criteria

- No modal PowerShell/WinForms exception dialogs during normal UI use.
- Every UI exception is caught, logged with stack/context, and reflected in status without terminating runtime.
- F7 window can resize/move/maximize and remains usable at minimum size.
- F7 is not forcibly re-centered after the user moves/resizes it.
- Opening every page, typing in every search box, changing every filter, selecting lists, and scrolling produces zero exceptions.
- Controls whose exact capability is false are disabled, not merely labeled OFF.
- No success/ON text appears before a matching native ACK/readback.
- Inventory reroll disabled when pointer is `0x0`.
- No hard-coded fake player coordinates.
- Source package does not recursively include prior package ZIPs.
- `Architect_Mod/Current` remains unchanged until user-approved runtime validation.
