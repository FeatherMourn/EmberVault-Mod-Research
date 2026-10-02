# CODE-0037D — Stable F7 Action/Control Binding + Truthfulness Closure

Working tree:

`H:\SteamLibrary\steamapps\common\Enshrouded\mods\architect_toolkit`

Target game build: `1076226`.

Do **not** modify or replace `Architect_Mod\Current`.

This task exists only to close the remaining F7 Truthfulness gate by making the current UI testable in a stable, behavior-based way.

Do not add gameplay features. Do not enable unsupported actions. Do not weaken fail-closed behavior. Do not package a runtime candidate unless the complete authoritative offline gate is fully green.

## Starting state

CODE-0037C ended **NOT QUALIFIED**.

Established:
- Skills production ASM defect fixed.
- Production-linked transparency harness: 8/8 PASS.
- Teleport remains fail-closed and the actual location teleport UI is disabled.
- Free Craft uses the approved native direct-patch readiness contract.
- Auto Loot remains resource/vanilla-path canary only.
- Simulated-E Auto Loot removed.
- `tuneGatherDrops = false`.
- Always Flying remains disabled.
- Old false Infinite Glider Stamina semantics remain unavailable.
- Current master: 162/163 invariants.
- Only failing suite: `F7 Truthfulness & Safety Contract`.
- Remaining failures: 31 legacy source-pattern assertions.
- CODE-0037C classified them `AMBIGUOUS_BLOCKED` because the current UI lacks a complete stable action-ID-to-control mapping for safe headless verification.
- Those assertions were not deleted or weakened.
- No final DLL/ZIP was built.
- `Architect_Mod\Current` was not changed.

## Objective

Add the **smallest possible production/testability binding** between an existing F7 action ID and the actual WinForms control representing that action, then rebuild the F7 Truthfulness suite around real control state plus real backend capability state.

This is not a UI redesign and not a new action registry.

The result must prove:

> Every visible F7 action control is truthfully enabled/disabled according to its approved backend capability, and unsupported actions cannot dispatch successfully.

## Part A — inspect current UI creation and registry first

Before editing:

1. Identify the canonical F7 action registry structure.
2. Identify every helper/function used to create action buttons, toggles, numeric controls, list actions, and other executable controls.
3. Identify how action IDs are currently passed into closures/handlers.
4. Identify any existing use of `Control.Tag`, dictionaries keyed by action ID, action metadata attached to controls, helper return objects, or page-local control maps.
5. Produce a short map of which control-construction helpers cover the 31 failing legacy assertions.

Do not create a second independent list of action IDs.

## Part B — add stable action-ID-to-control binding

Preferred implementation:

- Every executable F7 control that represents an Admin action must expose its canonical existing action ID through the actual control object.
- Use an existing safe field if possible, preferably `Control.Tag`.
- Also register the control in one Architect-owned map keyed by action ID, such as `$script:adminActionControls[actionId] = control`, only if no equivalent map already exists.

Requirements:
- The action ID must come from the existing canonical action/registry object already used to route the command.
- Do not duplicate hardcoded IDs in a new registry.
- Do not change user-visible labels solely for testing.
- Do not change runtime enablement logic solely for testing.
- Do not enable currently unsupported controls.
- The binding must be inert metadata only.
- Multiple controls for one action are allowed only where the current UI genuinely has them; map to a list and test all.
- Non-executable UI chrome must not be forced into the action map.
- If a helper currently receives only a callback, thread the existing canonical action ID through that helper from existing action metadata. Never infer IDs from visible button text.

## Part C — expose a read-only test snapshot

Add one small helper callable by the existing headless UI tests, for example `Get-AdminActionControlSnapshot`.

For every bound action control return:
- actionId
- control type
- enabled
- visible
- existing text/label
- existing tooltip/unavailable reason if tracked
- page/category if already known
- backend type from canonical action metadata
- capability/readiness result used for enablement

The helper must be read-only, dispatch nothing, and mutate no game/runtime state.

Prefer keeping it internal to `ArchitectRuntime.ps1` and callable through the existing dot-source/headless-test mechanism. Do not create new IPC.

## Part D — replace the 31 brittle assertions with behavioral checks

Run the old F7 Truthfulness suite first and preserve the exact 31 failures.

For every old assertion:
1. identify the action/control it intended to protect
2. map it to the real bound control
3. replace the source-pattern assertion with a behavioral assertion against real control state plus canonical backend/capability state

Do not delete assertions.

### Unsupported/unresolved action

For every action whose approved backend is NONE/unavailable/unproven, or whose readiness is false:
- all bound executable controls must have `Enabled == false`
- unavailable state/reason must be represented by the current UI mechanism
- direct offline dispatch must return rejected/unsupported/not-proven
- no fallback backend may run
- no optimistic success may be produced

### Supported action

For an approved supported action:
- control enablement must follow the real capability/readiness state
- readiness false in the headless fixture => disabled
- a controlled synthetic fixture may enable it only when the exact required readiness fields are true
- this proves UI/routing only, not runtime gameplay semantics

## Part E — exact special-case contracts

### Teleport
Must remain unavailable/fail-closed:
- bound teleport controls disabled
- dispatch rejected/not-proven
- no `WritePlayerCoordinates`
- no coordinate `WriteProcessMemory`
- no queued-success fallback
- no guessed player transform

### Free Craft
Approved direct-patch candidate:
- direct-patch/native patch-engine route
- enablement depends on `mutationBackendReady && patchFreeCraftReady`
- no dependency on `hookFrameworkReady`
- readiness false => UI disabled
- exact synthetic readiness true => UI may enable
- dispatcher resolves to Free Craft direct-patch route
- no raw fallback write

Do not claim runtime semantic proof.

### Auto Loot
Current approved state:
- resource/vanilla pickup-zone path
- canary scope
- `tuneGatherDrops = false`
- no simulated E-key/timer path

### Always Flying
Must remain unavailable.

### Infinite Glider Stamina
Must remain unavailable as a truthful infinite-stamina feature.

### Other unresolved actions
Do not bulk-enable Health, Mana, Stamina, item spawn, entity mutation, terrain mutation, prop mutation, or other unresolved actions.

## Part F — prove binding completeness

Add tests proving:
- every visible executable control created by F7 action-control helpers has a canonical action-ID binding
- every enabled executable F7 action control maps to exactly one canonical action definition
- no enabled action control is missing from the binding map
- no binding references an action absent from the canonical registry
- duplicate mappings are enumerated and justified
- intentionally unbound controls are non-executable UI chrome

If executable controls exist outside standard helpers, bind them using the same canonical mechanism or test/document them individually.

There must be zero hidden unbound clickable action controls.

## Part G — F7 Truthfulness suite output

The rewritten truthfulness suite must print:
- canonical actions inspected
- executable controls bound
- unsupported actions checked
- supported/readiness-gated actions checked
- direct dispatch rejection checks
- duplicate mappings
- unbound executable controls, which must be zero
- total invariants pass/fail

The suite must exit nonzero on any mismatch.

## Part H — final master gate

After truthfulness is green:

1. Run F7 Truthfulness alone.
2. Run the complete master suite.
3. Require 100% green.
4. If production source changed, synchronize identity to:
   - version: `0.41.0`
   - buildId: `architect-v041-f7-integration-code0037d-20260919`
   - retain the currently approved mode
5. Stop editing.
6. Run the complete master suite one final time against frozen source.
7. Only if green: build DLL, package ZIP, verify nested ZIP count = 0, extract cleanly, and rerun package verification.
8. No source/test edit may occur after the final green master run.

Verify extracted package still has:
- fixed Skills ASM
- stable F7 action/control binding
- behavior-based truthfulness tests
- zero unbound enabled executable F7 controls
- Teleport fail-closed
- no simulated-E Auto Loot
- Auto Loot canary
- `tuneGatherDrops = false`
- Always Flying disabled
- false Infinite Glider Stamina unavailable
- Free Craft direct-patch readiness gating
- CODE-0036 and CODE-0037 suites executed by master
- F7 Truthfulness executed by master
- synchronized CODE-0037D identity if production source changed

## Stop conditions

STOP without packaging if:
- any of the 31 assertions cannot safely map to a real action/control
- any executable control remains unbound
- any unsupported action remains enabled
- any required suite remains red
- action ID would have to be guessed from visible text
- the mapping would require a second action registry
- evidence is insufficient

Report the blocker instead of guessing.

## Final deliverable

Return `CODE-0037D_qualification_report.md` containing:
1. exact 31 initial legacy failures
2. canonical action registry location
3. UI control-construction helper locations
4. exact binding implementation
5. production files changed
6. every old assertion -> new behavioral assertion mapping
7. proof no safety assertion was weakened
8. binding completeness results
9. F7 Truthfulness pass/count
10. full master suite breakdown and total
11. final version/buildId/mode
12. DLL SHA256 + byte size
13. ZIP SHA256 as one uninterrupted 64-character lowercase hex string + byte size
14. nested ZIP count
15. extracted-package verification
16. explicit statement that `Architect_Mod\Current` was not replaced
17. runtime-test instructions only if every offline gate is green

Do not claim runtime proof from compilation or offline tests.
