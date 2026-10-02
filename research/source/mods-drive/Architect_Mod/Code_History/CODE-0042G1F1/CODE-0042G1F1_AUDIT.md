# CODE-0042G1F1 — F7 shell UI/lifetime audit

Date: 2026-09-20
Build scope: Enshrouded 1076226
Status: SOURCE-AUDITED / PARTIAL SHELL MIGRATION / NO RUNTIME CLAIM

## Source-verified
- `LifetimeScope` is now part of stable F7 event definitions and active bindings.
- `Register-F7EventDefinition`, `Register-F7UiEvent`, `Register-AdminActionEvent`, and `Bind-AdminActionControl` accept/propagate PAGE vs SHELL lifetime.
- The migrated shell events use `LifetimeScope="SHELL"`:
  - bounds timer Tick
  - ResizeEnd
  - LocationChanged
  - bounds-save FormClosing
  - 11 navigation button Click events
  - Escape KeyDown
  - hide/cancel FormClosing
- Registry remains 54 unique actions.
- Home, Player, and Mobility raw-event migrations remain preserved.
- AOB Scanner remains intentionally raw and invokes `NativeMemoryEngine.ToggleScanner()`.

## Remaining shell UI-only raw event
One clearly UI-only F7 shell handler was missed:

`$adminContent.Add_SizeChanged({ Resize-AdminPageChildren })`

This is persistent shell/layout behavior and should be migrated through `Register-F7UiEvent` with SHELL lifetime, e.g.:

- EventId: `f7.shell.content.sizeChanged`
- Page: `Shell`
- Operation: `ResizeAdminPageChildren`
- Classification: UI_ONLY
- LifetimeScope: SHELL

Therefore the current shell raw-event state is not yet:
- UI_ONLY raw = 0
- ACTION raw = 1

It is currently:
- UI_ONLY raw = 1 (`adminContent.SizeChanged`)
- ACTION raw = 1 (AOB Scanner)

## Lifecycle defect in Clear-AdminContent
Current source removes a binding only when:

`LifetimeScope != SHELL AND Control exists AND Control.IsDisposed == false`

This means:
- a disposed PAGE binding is NOT removed;
- a missing/null PAGE binding is NOT removed;
- a disposed SHELL binding is also preserved.

That contradicts the intended rule that disposed controls are never preserved and can leave stale entries in `$script:f7ActiveBindings`.

Required behavior:
1. remove any binding whose Control is null or disposed;
2. remove every remaining PAGE binding;
3. preserve only live SHELL bindings;
4. rebuild `$script:adminActionControls` only from the surviving live active ACTION bindings.

Because not every shell event source is a WinForms `Control` (for example the Timer), liveness checks should be property-safe and must not assume every component exposes `IsDisposed`.

## AOB Scanner remains a separate ACTION problem
Do not migrate scanner in the same repair.

Current scanner behavior is not UI-only:
- `ToggleScanner()` starts/stops the memory sweeper;
- scanner disable calls `UninstallPositionHook()` and `RevertAll()`;
- the sweeper can resolve patches and tick autorun/auto-loot when those states are active.

It needs a separate canonical fail-closed decision after shell lifetime correctness is green.

## Acceptance for next repair
Before scanner canonicalization:
- migrate `adminContent.SizeChanged` as SHELL/UI_ONLY;
- shell UI-only raw registrations = 0;
- shell ACTION raw registrations = 1, exactly AOB Scanner;
- `Clear-AdminContent` prunes null/disposed bindings and all PAGE bindings;
- only live SHELL bindings survive;
- no stale/disposed active bindings after page transitions;
- registry remains 54;
- Home/Player/Mobility raw counts remain 0;
- existing safety restrictions remain unchanged.
