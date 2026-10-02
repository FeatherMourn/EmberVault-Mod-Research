# CODE-0037E — Canonical F7 Action Binding Refactor

Working tree:

`H:\SteamLibrary\steamapps\common\Enshrouded\mods\architect_toolkit`

Target game build: `1076226`.

Do **not** modify or replace:

`Architect_Mod\Current`

This task is a narrow internal refactor to unblock the F7 Truthfulness gate.

Do not add gameplay features.
Do not enable unsupported actions.
Do not weaken fail-closed behavior.
Do not package a runtime candidate unless every authoritative offline suite is green.

## Starting state

CODE-0037D ended `BLOCKED / NOT QUALIFIED`.

Known facts:
- Skills production transparency defect is fixed; production-linked harness passes 8/8.
- Teleport remains fail-closed and its actual UI control is disabled.
- Free Craft is an approved native direct-patch candidate and uses the direct-patch readiness contract.
- Auto Loot remains vanilla/resource canary only.
- simulated-E Auto Loot is removed.
- `tuneGatherDrops = false`.
- Always Flying remains disabled.
- old false Infinite Glider Stamina semantics remain unavailable.
- Master remains 162/163.
- Only failing suite: `F7 Truthfulness & Safety Contract`.
- It still contains 31 legacy source-pattern failures.
- CODE-0037D found no complete canonical action-ID-to-control binding.
- `Register-SafeUiEvent` receives closures without action IDs.
- many controls lack `Tag`.
- no complete action-control map exists.
- several handlers contain literal command/action strings.
- no CODE-0037D changes were made.

## Objective

Refactor F7 control creation and event wiring so every executable Admin control is bound to the **same canonical action ID that its command route actually uses**.

The key rule is:

> Do not infer action IDs from labels. Recover them from the existing command route / registry and thread them explicitly through control creation.

This is a production-code structural cleanup, not a feature change.

## Part A — identify the canonical source of truth

Before editing, locate the existing canonical action definitions/registry used by the current F7 system.

For each action definition identify:
- canonical action ID
- backend type
- readiness/capability metadata
- dispatch handler or route
- current UI page/category references if present

Do not create a new independent list of action IDs.

If the current registry has aliases or normalized IDs, document which field is the canonical dispatch ID.

## Part B — inventory all executable F7 controls

Enumerate every executable control in F7:
- buttons
- checkboxes/toggles
- numeric apply buttons
- combo/list actions
- preset buttons
- any control whose interaction can call `Send-CheatCommand`, `Send-AdminCommand`, `Invoke-*`, or another mutation/dispatch path

For each control record:
- source location
- helper used to construct it
- handler/closure source
- literal action/command string if present
- matching canonical action definition
- whether mapping is exact
- whether mapping is ambiguous

STOP if any executable control cannot be matched exactly to an existing canonical action route without guessing.

## Part C — eliminate literal action strings from handlers

Where an event handler currently contains a literal command string that matches an existing canonical action ID:

Before:
`Send-CheatCommand "cheat.world.build_range" ...`

Refactor so the action ID is supplied from the canonical action object/lookup and threaded into the helper/closure.

The literal string may remain only in the canonical registry/definition source.

Do not duplicate the same ID in UI code.

If the UI is currently built by hardcoded per-page code, minimally resolve the canonical action object by exact existing ID once, then pass that action object or its canonical ID into the helper.

Never derive the ID from visible button text.

## Part D — standardize executable control construction

Introduce or extend a small common binding helper, e.g.:

`Register-AdminActionControl -Action $action -Control $control`

or equivalent.

It must:
- require a canonical existing action object/ID
- set inert metadata on the control, preferably `Tag`
- register the control into one action-control map
- preserve existing event behavior
- preserve existing labels/layout
- preserve existing capability gating
- preserve existing command lifecycle

Suggested map shape:

`$script:adminActionControls[actionId] -> list of controls`

Use a list because one action may legitimately have multiple controls.

Do not replace the existing action registry.

## Part E — thread action identity through event registration

Where `Register-SafeUiEvent` currently receives only a closure:
- keep its error-boundary behavior intact
- add action identity only where the event is an Admin action
- do not require action IDs for non-action UI events

Preferred approaches:
- closure captures canonical `$action.Id`
- helper receives `-ActionId`
- binding is established before handler registration

Do not change exception handling, UI safety boundaries, or threading behavior except as necessary to carry inert action identity.

## Part F — completeness guard

Add an internal read-only function:

`Get-AdminActionControlSnapshot`

Return for every bound control:
- actionId
- control type
- enabled
- visible
- text
- page/category if known
- backend
- capability/readiness result
- unavailable reason if tracked

Also detect:
- enabled executable controls with no action binding
- action bindings whose ID is absent from canonical registry
- duplicate mappings
- executable controls whose handler route does not match the bound action ID

The snapshot must not dispatch or mutate.

## Part G — route-consistency verification

Add tests that prove:

1. bound action ID == actual dispatch ID used by the event handler
2. no handler uses a literal action string outside the canonical registry/definition layer
3. every enabled executable Admin control has a canonical binding
4. every binding points to a canonical action
5. unsupported/unready actions are disabled
6. direct offline dispatch for unsupported actions rejects/fails closed
7. Free Craft binds to its canonical direct-patch action
8. Teleport controls remain bound but disabled/unavailable if visible
9. Always Flying remains unavailable
10. Infinite Glider Stamina remains unavailable
11. no simulated-E Auto Loot route exists

If a UI helper cannot be safely converted without behavior change, STOP and report the exact helper/control.

## Part H — replace the 31 legacy assertions

Only after the binding/completeness tests are green:

- preserve the exact list of 31 old assertions
- replace each one with a behavioral assertion against the real bound control + canonical action metadata + actual readiness state
- include a one-to-one migration table:
  - old assertion
  - protected action/control
  - new behavioral assertion
  - why it is equal or stricter in safety intent

Do not delete assertions without replacement.

## Part I — final qualification

After the final source/test edit:

1. run F7 Truthfulness alone
2. require 100% green
3. run complete master suite
4. require 100% green
5. if production source changed, synchronize identity to:
   - version: `0.41.0`
   - buildId: `architect-v041-f7-integration-code0037e-20260919`
   - retain currently approved mode
6. freeze source
7. rerun master once more after identity synchronization
8. only if green:
   - build DLL
   - package ZIP
   - nested ZIP count = 0
   - extract final ZIP
   - rerun package/extracted-source verification
9. no source/test edit after final green master

## Stop conditions

STOP without packaging if:
- any executable control cannot be mapped exactly
- any route still requires guessing from UI text
- any unsupported action is enabled
- any handler route disagrees with the bound action ID
- any required suite remains red
- refactor would require a second action registry
- the action/control map cannot be made complete without redesigning the whole UI

## Final deliverable

Return `CODE-0037E_qualification_report.md` with:

1. canonical action registry location
2. inventory of executable F7 controls
3. every literal action string removed from UI handlers
4. exact binding helper implementation
5. exact action-control map implementation
6. route-consistency results
7. completeness results
8. migration table for all 31 old truthfulness assertions
9. proof no safety property was weakened
10. F7 Truthfulness pass/count
11. full master suite breakdown
12. final version/buildId/mode
13. DLL SHA256 + byte size
14. ZIP SHA256 as one uninterrupted 64-char lowercase hex string + byte size
15. nested ZIP count
16. extracted-package verification
17. explicit statement that `Architect_Mod\Current` was not replaced
18. runtime-test instructions only if every offline gate is green

Do not claim runtime proof from compilation/offline tests.
