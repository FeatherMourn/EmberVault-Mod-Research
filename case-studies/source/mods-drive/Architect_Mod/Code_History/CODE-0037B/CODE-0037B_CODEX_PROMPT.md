# CODE-0037B — Transparency + Truthfulness Closure

You are working in the separate Architect Toolkit working tree:

`H:\SteamLibrary\steamapps\common\Enshrouded\mods\architect_toolkit`

Target game build: `1076226`.

Do **not** modify or replace `Architect_Mod\Current`.

This is a qualification/repair pass only. Do not add new gameplay features, do not broaden the supported feature set, and do not package a runtime candidate unless the final offline gate is fully green.

## Current state from CODE-0037A

Already reported:
- CODE-0036: 15/15 PASS
- CODE-0037: 6/6 PASS
- ADM-TEST-0002 Teleport Disarmament: 15/15 PASS
- PowerShell AST: 4/4 PASS
- C# compile runner corrected to use `tests\test_compile.ps1`
- Teleport location UI regression fixed
- Free Craft truthfulness expectation updated to approved direct-patch behavior
- Teleport coordinate writes remain disarmed
- simulated-E Auto Loot remains removed
- Auto Loot remains `scope = "canary"`
- `tuneGatherDrops = false`
- Always Flying remains disarmed
- false old Infinite Glider Stamina semantics remain unavailable
- Free Craft native direct-patch path remains preserved

Remaining blockers:
1. Synthetic Hook Transparency Harness: Skills hook mismatches `r1` and `r5`.
2. F7 Truthfulness & Safety Contract: remaining failures are legacy unsupported-control expectations and have not been waived.

The build is **NOT QUALIFIED**.

## Non-negotiable rules

1. Do not turn tests green by weakening safety assertions.
2. Do not delete failing tests merely because they are inconvenient.
3. Do not mark a feature supported unless current production routing really supports it.
4. Do not enable Teleport, Always Flying, the old Glider Stamina control, or any other previously unsupported feature.
5. Do not invent Enshrouded offsets, pointers, signatures, calling conventions, or semantics.
6. Do not change `Architect_Mod\Current`.
7. Do not package a runtime candidate if any authoritative suite remains red.
8. The final master run must occur after the last source/test edit.
9. If production behavior and a test conflict, prove which side is stale before changing it.
10. Compilation is not runtime proof.

## Part A — reproduce failures exactly

Before changing anything, run the full current master suite and save full stdout/stderr.

Record every failing invariant with:
- suite name
- invariant/test name
- expected behavior
- actual behavior
- relevant production source path
- relevant test path

For F7 Truthfulness, list every remaining failing assertion individually.

For transparency, capture exact before/after values for `r1` and `r5` and identify what those labels represent in the production hook context.

## Part B — Skills hook transparency

Do not redesign the hook framework. Diagnose only the Skills hook.

### Bind the harness to production

Identify:
- production Skills hook entry RVA/signature
- exact stolen bytes
- overwrite length
- detour encoding
- trampoline/continuation address
- actual production assembly stub
- exact harness path that claims to test that stub

Prove the harness executes/emulates the actual production assembly, not a stale synthetic approximation. If it does not, repair harness linkage first and rerun before editing assembly.

### Decode r1/r5 and find first divergence

For each mismatch report:
- incoming value
- value immediately before Architect hook body
- value immediately after hook body
- value after stolen-instruction replay
- value at continuation
- expected vanilla value at the same point

Identify the first instruction where Architect diverges from vanilla-equivalent execution.

Do not excuse a mismatch merely because a register is ABI-volatile. Transparency means the continuation state must match vanilla except for explicitly intended feature semantics.

### Audit known hazards

Check for:
- `mov rax, imm64 / jmp rax` or other register-clobbering detours
- scratch-register use not restored
- incorrect push/pop ordering
- stack alignment changes
- relevant flags clobbering
- wrong stolen-instruction replay
- bad RIP-relative relocation
- nonvolatile GPR preservation errors
- XMM6-XMM15 preservation errors if touched
- continuation into the middle of an instruction
- double-executed or skipped stolen bytes
- hook enable/disable leakage into test setup

Use the approved register-neutral 14-byte `FF 25 [RIP+0] + absolute address` detour where appropriate. Do not reintroduce the disproven `mov rax/jmp rax` detour.

Classify the transparency failure as exactly one:
- `PRODUCT_ASM_DEFECT`
- `HARNESS_NOT_TESTING_PRODUCTION_ASM`
- `HARNESS_EXPECTATION_STALE`
- `AMBIGUOUS_BLOCKED`

If product defect: make the smallest fix and rerun production-linked transparency.
If harness linkage defect: fix the harness, not working assembly.
If stale expectation: prove vanilla-equivalent continuation state before updating it.
If ambiguous: leave red and stop.

Required result: production-linked Skills transparency passes bit-for-bit at the continuation boundary.

## Part C — F7 Truthfulness failures

For every remaining failure, create a table with:
- assertion/test name
- UI/action ID
- backend route
- old expected behavior
- current actual behavior
- approved CODE-0037 behavior
- classification: `PRODUCT_REGRESSION`, `STALE_TEST`, or `AMBIGUOUS_BLOCKED`
- exact fix

Approved rules:

### Teleport
Must remain unavailable/fail-closed:
- UI not executable
- no coordinate write
- no queued-success fallback
- no guessed player transform
- dispatcher returns explicit unsupported/not-proven result

If product still presents it as available, fix product.

### Free Craft
This is the one approved behavior that changed from old unsupported/hook-backed expectations.

It is now an intentional native direct-patch candidate and must route through:
- exact build fingerprint
- `mutationBackendReady`
- `patchFreeCraftReady`
- ArchitectPatchEngine apply/revert
- immediate readback
- truthful state publication
- no hook-framework dependency
- no raw fallback write

Tests that still require Free Craft to be unsupported/hook-backed are stale only if production source satisfies this exact contract.

### Auto Loot
Approved current state:
- vanilla/resource composition only
- canary scope
- `tuneGatherDrops = false`
- no simulated E-key/timer path

Do not mark full-scope Auto Loot or gather tuning proven.

### Always Flying
Must remain disabled/unavailable.

### Infinite Glider Stamina
The old `0x39E73C` behavior must not be exposed as true Infinite Glider Stamina.

### Other legacy unsupported controls
Do not bulk-convert old unsupported assertions to supported. Inspect registry/backend individually. If no approved backend exists, UI must stay disabled/unavailable.

Do not enable Health, Mana, Stamina, Flight, Teleport, item spawn, entity mutation, or other unresolved features.

## Part D — master runner authority

Verify `build_scripts\run_all_tests.ps1` executes the real authoritative suites, including:
- PowerShell AST
- C# compile-only `tests\test_compile.ps1`
- ADM-TEST-0002
- F7 Truthfulness & Safety Contract
- production-linked hook transparency
- patch-engine/lifecycle tests
- CODE-0036 integration suite
- CODE-0037 hardening suite

Master must fail nonzero if any required suite fails. Report exact invariant counts from each suite.

## Part E — identity

If production source changes in CODE-0037B, synchronize:
- version: `0.41.0`
- buildId: `architect-v041-f7-integration-code0037b-20260919`
- mode: retain the currently approved mode unless the authoritative identity source requires synchronized equivalent wording

Ensure identity JSON/header/native runtime/injector expectations agree.

## Part F — final freeze

Only after all failures are resolved:
1. stop editing source/tests
2. run complete master suite and require 100% green
3. record suite-by-suite counts
4. build DLL from exact unchanged source
5. package exact unchanged source
6. nested ZIP count must be 0
7. extract final ZIP cleanly
8. rerun applicable package/extracted-source verification
9. verify extracted package has:
   - Teleport hard-disabled
   - no reachable Teleport coordinate write
   - no simulated-E Auto Loot
   - Auto Loot canary
   - `tuneGatherDrops=false`
   - Always Flying disabled
   - false old Glider Stamina semantics unavailable
   - Free Craft direct-patch route/readiness
   - CODE-0036 + CODE-0037 in master
   - synchronized CODE-0037B identity if source changed
10. confirm no source/test edit after final green master

If anything remains red, stop and do not package as qualified.

## Deliverable

Return one CODE-0037B qualification report with:
1. exact initial failing invariants
2. Skills transparency root cause and first incorrect instruction/state
3. Skills classification
4. every F7 Truthfulness failure and classification
5. exact files changed and why
6. exact tests changed and why each was legitimate
7. final suite-by-suite counts
8. final total invariants passed
9. final version/buildId/mode
10. DLL SHA256 + byte size
11. ZIP SHA256 as one uninterrupted 64-char lowercase hex string + byte size
12. nested ZIP count
13. extracted-package verification results
14. explicit statement that `Architect_Mod\Current` was not replaced
15. runtime-test instructions only if every authoritative offline gate is green

Do not claim runtime proof from compilation or offline tests.
