# CODE-0037C — F7 Truthfulness Contract Rebuild + Final Offline Gate

Working tree:

`H:\SteamLibrary\steamapps\common\Enshrouded\mods\architect_toolkit`

Target game build: `1076226`.

Do **not** modify or replace:

`Architect_Mod\Current`

This is a qualification/repair pass only. Do not add gameplay features, do not enable previously unsupported actions, and do not package a runtime candidate unless the final authoritative offline gate is fully green.

## Starting evidence

CODE-0037B result:

- Skills transparency root cause was a real production ASM defect.
- Production Skills entry was unconditionally reassigning `r9d`, `rsi`, and `rbx` after stolen-prologue replay while the feature was inactive.
- `runtime\native\source\ArchitectCheatCorrelationEntry.asm` was corrected.
- Production-linked transparency harness: **8/8 PASS**.
- Teleport location UI was disabled.
- Teleport fail-closed behavior remains required.
- Free Craft validation now targets the approved direct-patch contract.
- C# compile-only suite is corrected.
- ADM-TEST-0002 validates current teleport UI/fail-closed behavior.
- Final master result: **162/163**.
- Only failing suite family: **F7 Truthfulness & Safety Contract**.
- The remaining failures are described as legacy unsupported-control UI assertions that do not match the current UI implementation.
- They were deliberately not bulk-converted or weakened.
- No post-fix DLL/ZIP was produced.
- `Architect_Mod\Current` was not changed.

The build is **NOT QUALIFIED**.

---

# Objective

Close the F7 Truthfulness gate by replacing brittle or stale assertions only where they are demonstrably inconsistent with the current approved product contract.

The resulting suite must still prove this core rule:

> Architect must never present an unsupported or unverified F7 action as usable, successful, or available.

Do **not** solve this by deleting the truthfulness suite, changing it to a file-exists check, or making all controls pass unconditionally.

---

# Part A — enumerate every remaining truthfulness failure

Run only the current F7 Truthfulness suite first, unchanged.

Capture every failing assertion individually.

For each failure record:

- assertion/test name
- action/control name
- action ID if one exists
- category/page
- old expected UI/source pattern
- current actual UI/source pattern
- current backend route
- current capability/readiness state
- whether the control is actually enabled at runtime/headless UI construction
- whether invoking it can dispatch a command
- classification:
  - `PRODUCT_REGRESSION`
  - `STALE_STATIC_ASSERTION`
  - `AMBIGUOUS_BLOCKED`

Do not proceed to bulk edits until this table exists.

---

# Part B — establish the authoritative F7 truthfulness model

The authoritative truth model should come from the current product structures, not old source-text shapes.

Inspect the current implementation of:

- Admin action registry / action metadata
- backend type / route
- `canExecute` / availability / readiness fields
- `Get-AdminCapabilities`
- F7 page/control construction
- control `Enabled` state
- disabled/unavailable labels and tooltips
- command dispatcher routing
- native readiness flags
- pending/verified/rejected command lifecycle

Determine the smallest stable set of fields that defines whether a control may be executable.

Do not invent new backend semantics.

## Required semantic rule

For every F7 action exposed in the UI:

### Supported / executable
A control may be enabled only if its approved backend-specific readiness contract is satisfied.

Examples:

**Free Craft**
- native direct-patch backend
- build supported/fingerprint valid
- `mutationBackendReady == true`
- `patchFreeCraftReady == true`
- no dependency on `hookFrameworkReady`
- command route exists
- state is published truthfully

**Existing proven direct patches**
- use their specific `patch*Ready` flag
- mutation backend ready
- not in recovery-required state
- exact route exists

**Hook-backed controls**
- enabled only when the required hook/backend readiness is actually true

### Unsupported / unresolved
A control must be non-executable when no approved backend exists.

This includes, unless current approved evidence says otherwise:

- Teleport
- Always Flying
- old Infinite Glider Stamina semantics
- unresolved Health/God mutation paths
- unresolved Mana/Stamina player-authority paths
- unsupported item spawn/clear paths
- unresolved entity mutation paths
- unsupported terrain/prop mutations
- any other registry action whose approved backend is `NONE`, unavailable, unproven, or runtime-gated false

Unsupported actions may remain visible in the Codex/UI, but must be visibly unavailable and must fail closed if dispatch is attempted.

---

# Part C — repair the test architecture, not just the strings

The prior F7 Truthfulness suite appears to contain legacy source-pattern assertions.

Replace only the stale/brittle portions with tests that validate **behavioral truthfulness** against the current UI/registry architecture.

Preferred test hierarchy:

1. **Registry/backend truth**
   - enumerate F7 actions
   - verify backend + capability metadata
   - verify unsupported actions cannot report executable
   - verify supported actions have exact required readiness gate

2. **Headless UI truth**
   - instantiate the actual F7 UI/pages using the existing headless WinForms test infrastructure
   - inspect the real control bound to each action
   - verify `Enabled` matches the authoritative capability state
   - verify unavailable controls communicate unavailable/unsupported status through the existing label/tooltip/status mechanism
   - do not merely regex source code for button-construction syntax

3. **Dispatch truth**
   - for unsupported actions, direct dispatch must return rejected/unsupported/not-proven and must not mutate
   - for supported actions, route must resolve to the intended backend
   - this is an offline routing assertion, not a claim that gameplay semantics are runtime-proven

If the existing UI architecture already carries action IDs in `Tag`, metadata, closures, dictionaries, or control registries, use that.

If no stable mapping exists, make the smallest testability-only change that exposes existing action identity to the headless test without changing user-visible behavior or enabling anything. Do not invent a second action registry.

---

# Part D — special cases that must remain exact

## Teleport

Required:
- location teleport UI disabled/unavailable
- no direct coordinate write reachable
- no queued-success fallback
- no fake coordinates
- no guessed transform
- dispatch rejected/not-proven

Do not alter this contract to satisfy the suite.

## Free Craft

Required:
- this is now an approved direct-patch candidate
- UI may be executable only when current direct-patch readiness says so
- must use `patchFreeCraftReady`
- must use `mutationBackendReady`
- must not depend on monolithic hook readiness
- must not use raw fallback writes
- state publication must be truthful

The truthfulness suite should test this exact contract.

## Auto Loot

Current approved state:
- resource/vanilla pickup-zone path only
- `scope = "canary"`
- `tuneGatherDrops = false`
- no simulated `E` ownership

Do not mark full-scope Auto Loot proven.

## Always Flying

Must remain unavailable in F7 for this build.

## Infinite Glider Stamina

Must remain unavailable as a truthful "Infinite Glider Stamina" feature because the previous `0x39E73C` target was user-disproven for that semantic.

---

# Part E — classification rule for each stale assertion

For every assertion you change, provide:

- old assertion
- why it is stale
- what current production architecture replaced the old pattern
- new assertion
- why the new assertion is at least as strict about unsupported controls

A test change is legitimate only if the new test verifies the same safety property more accurately.

Examples of legitimate replacements:

- old: "source must contain `$button.Enabled = $false` next to a specific button declaration"
- new: "headless-instantiated control for action X is disabled whenever capability X is false"

- old: "Free Craft must be unsupported"
- new: "Free Craft is disabled unless `mutationBackendReady && patchFreeCraftReady`; route is direct patch and does not depend on hook framework"

Examples of illegitimate weakening:

- deleting the assertion
- accepting either enabled or disabled
- checking only that the action exists
- checking only that a tooltip string exists
- marking all unknown controls as supported
- bypassing the UI and testing only registry metadata while the actual control remains clickable

---

# Part F — rerun and freeze

After the final truthfulness repair:

1. Run the F7 Truthfulness suite alone.
2. Require all of its individual assertions to pass.
3. Run the complete master suite.
4. Require **100% green**.
5. Record suite-by-suite counts and final total.
6. If any production source changed, synchronize identity to:

   - version: `0.41.0`
   - buildId: `architect-v041-f7-integration-code0037c-20260919`
   - mode: retain the currently approved mode

7. Stop editing.
8. Build the DLL from the exact final source.
9. Package from the exact final source.
10. Verify nested ZIP count = 0.
11. Extract final ZIP to a clean directory.
12. Run all applicable extracted-package verification.
13. Verify final extracted source still contains:
   - fixed Skills transparency assembly
   - Teleport unavailable/fail-closed
   - no reachable teleport coordinate write
   - no simulated-E Auto Loot
   - Auto Loot canary
   - `tuneGatherDrops = false`
   - Always Flying unavailable
   - false Infinite Glider Stamina unavailable
   - Free Craft direct-patch gating
   - CODE-0036 and CODE-0037 suites executed by master
   - current truthfulness suite executed by master
   - synchronized CODE-0037C identity if production source changed
14. Confirm no source/test edit occurred after the final green master run.

If any authoritative suite remains red, STOP and report it. Do not package as qualified.

---

# Final deliverable

Return one `CODE-0037C_qualification_report.md` containing:

1. Every initial F7 Truthfulness failing assertion.
2. Per-assertion classification.
3. The authoritative truthfulness model you derived from current production architecture.
4. Every production-code change.
5. Every test change, with justification.
6. Proof unsupported controls remain unavailable.
7. Proof Free Craft uses the approved direct-patch readiness contract.
8. Final F7 Truthfulness assertion count/pass count.
9. Final master suite breakdown and total.
10. Final version/buildId/mode.
11. DLL SHA256 + byte size.
12. ZIP SHA256 as one uninterrupted 64-character lowercase hex string + byte size.
13. Nested ZIP count.
14. Extracted-package verification results.
15. Explicit statement that `Architect_Mod\Current` was not replaced.
16. Runtime-test instructions only if all offline gates are green.

Do not claim runtime proof from offline tests.
